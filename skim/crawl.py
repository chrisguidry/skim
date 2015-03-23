#!/usr/bin/env python
#coding: utf-8
from datetime import datetime, timezone
import json
import logging
import multiprocessing
import os
import re
import sys
import time

import feedparser

from skim import __version__, index
from skim.configuration import elastic, INDEX
from skim.markup import to_text
from skim.subscriptions import subscriptions

feedparser.USER_AGENT = 'Skim/{} +https://github.com/chrisguidry/skim/'.format(__version__)

logger = logging.getLogger(__name__)


def conditional_get_state(feed_url):
    doc = elastic().get_source(index=INDEX, doc_type='feed', id=feed_url,
                               _source=['etag', 'modified'], ignore=[404])
    if not doc:
        return None, None
    return doc['etag'], doc['modified']

def save_conditional_get_state(feed_url, etag, modified):
    elastic().update(index=INDEX, doc_type='feed', id=feed_url, body={
        'doc': {
            'url': feed_url,
            'etag': etag,
            'modified': modified
        },
        'doc_as_upsert': True
    })

def save_feed(feed_url, feed):
    elastic().update(index=INDEX, doc_type='feed', id=feed_url, body={
        'doc': {
            'url': feed_url,
            'title': feed.get('title', feed_url),
            'subtitle': feed.get('subtitle')
        },
        'doc_as_upsert': True
    })

def entry_exists(entry_url):
    return elastic().exists(index=INDEX, doc_type='entry', id=entry_url)

def save_entry(feed_url, entry):
    elastic().index(index=INDEX, doc_type='entry', id=entry_url(feed_url, entry), body={
        'feed': feed_url,
        'url': entry_link(entry),
        'title': entry_title(entry),
        'published': entry_time(entry).isoformat() + 'Z',
        'text': entry_text(entry),
        'image': entry.get('image', {}).get('href'),
        'enclosures': [{'type': enc.type, 'url': enc.href}
                       for enc in entry.get('enclosures') or []]
    })

def entry_url(feed_url, entry):
    return entry_link(entry) or '{}#{}'.format(feed_url, entry_time(entry).isoformat() + 'Z')

def entry_link(entry):
    if 'enclosures' in entry:
        for enclosure in entry['enclosures']:
            if enclosure.get('type').startswith(('audio/', 'video/')) and enclosure.get('href'):
                return enclosure['href']
    return entry['link']

def entry_title(entry):
    title = entry.get('title')
    if not title:
        return '[untitled]'
    return to_text(None, None, title)

def entry_time(entry):
    try:
        return entry['__date__']
    except KeyError:
        pass

    entry_time = entry.get('published_parsed', entry.get('updated_parsed'))
    if entry_time:
        entry_time = datetime(*entry_time[0:6])

    if not entry_time:
        logger.warn('Guessing date for entry lacking a timestamp: %r', entry_link(entry))
        entry_time = guess_time_from_url(entry_link(entry))

    if not entry_time:
        logger.warn('Substituting now for entry lacking a timestamp: %r', entry_link(entry))
        entry_time = datetime.utcnow()

    if entry_time > datetime.utcnow():
        logger.warn('Entry from the future; using now: %r', entry_link(entry))
        entry_time = datetime.utcnow()

    entry['__date__'] = entry_time

    return entry_time

def guess_time_from_url(url):
    match = re.search('((?P<year>2(\d{3}))/(?P<month>\d{1,2})(/(?P<day>\d{1,2}))?)', url)
    if match:
        return datetime(int(match.group('year')), int(match.group('month')), int(match.group('day') or '1'))

def entry_text(entry):
    content = ''
    if 'content' in entry:
        content = entry.content[0]
    elif 'summary_detail' in entry:
        content = entry.summary_detail
    else:
        return ''

    return to_text(content.base, entry_link(entry), content.value)

def crawl(feed_url):
    logger.info('Crawling %r...', feed_url)

    etag, modified = conditional_get_state(feed_url)
    parsed = feedparser.parse(feed_url, etag=etag, modified=modified)
    if not parsed.get('status'):
        logger.warn('No status returned while crawling %s.  Parsed: %r', feed_url, parsed)
        return

    if parsed.status == 304:
        logger.info('Feed %s reported 304', feed_url)
        return

    if parsed.status not in (200, 301, 302):
        logger.warn('Status %s while crawling %s.', parsed.status, feed_url)
        return

    save_feed(feed_url, parsed.feed)

    for entry in parsed.entries:
        new_entry_url = entry_url(feed_url, entry)
        if entry_exists(new_entry_url):
            logger.info('%s has already been seen', new_entry_url)
            continue

        logger.info('New entry %s on %s', new_entry_url, feed_url)
        save_entry(feed_url, entry)

    save_conditional_get_state(feed_url, parsed.get('etag'), parsed.get('modified'))

def crawl_all(feed_urls, wait=True):
    pool = multiprocessing.Pool(16)
    results = []
    for feed_url in feed_urls:
        logger.info('Queueing %s', feed_url)
        results.append(pool.apply_async(crawl, [feed_url]))
    pool.close()

    if not wait:
        return
    for result in results:
        result.get()
    pool.join()

def recrawl(feed_url):
    es = elastic()
    from skim.entries import by_feed
    for entry in by_feed(feed_url):
        es.delete(index=INDEX, doc_type='entry', id=entry['url'])
    save_conditional_get_state(feed_url, None, None)
    crawl(feed_url)


if __name__ == '__main__':
    index.ensure()

    crawl_all(sys.argv[1:] or [s['url'] for s in subscriptions()])
