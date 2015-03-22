#!/usr/bin/env python
#coding: utf-8
from datetime import datetime, timezone
import logging
import multiprocessing
import os
import sys
import time

import feedparser
import html2text
from slugify import slugify

from skim import __version__, key, logging_to_console, index
from skim.configuration import elastic, INDEX
from skim.subscribe import subscriptions

feedparser.USER_AGENT = 'Skim/{} +https://github.com/chrisguidry/skim/'.format(__version__)
html2text.config.UNICODE_SNOB = 1
html2text.config.SINGLE_LINE_BREAK = False
HTML2TEXT_CONFIG = {'bodywidth': 0}

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

def save_headers(feed_url, headers):
    elastic().update(index=INDEX, doc_type='feed', id=feed_url, body={
        'doc': {
            'url': feed_url,
            'headers': headers
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
        'url': entry.get('link'),
        'title': entry_title(entry),
        'published': entry_time(entry).isoformat() + 'Z',
        'text': entry_text(entry)
    })

def entry_url(feed_url, entry):
    return entry.get('link') or '{}#{}'.format(feed_url, entry_time(entry).isoformat() + 'Z')

def entry_title(entry):
    title = entry.get('title')
    if not title:
        return '[untitled]'
    return html2text.html2text(title, **HTML2TEXT_CONFIG).strip()

def entry_time(entry):
    try:
        return entry['__date__']
    except KeyError:
        pass

    entry_time = entry.get('updated_parsed', entry.get('published_parsed'))
    if entry_time:
        entry_time = datetime(*entry_time[0:6])
    else:
        logger.warn('Substituting now for entry lacking a timestamp: %r', entry.get('link'))
        entry_time = datetime.utcnow()

    if entry_time > datetime.utcnow():
        logger.warn('Entry from the future; using now: %r', entry.get('link'))
        entry_time = datetime.utcnow()

    entry['__date__'] = entry_time

    return entry_time

def entry_text(entry):
    content = ''
    if 'content' in entry:
        content = entry.content[0]
    elif 'summary_detail' in entry:
        content = entry.summary_detail
    else:
        return ''

    if not content.base.strip():
        console.warn('No baseurl for entry %r', entry)

    return html2text.html2text(content.value, baseurl=content.base, **HTML2TEXT_CONFIG)

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

    save_headers(feed_url, parsed.headers)
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

def crawl_all(feed_urls):
    pool = multiprocessing.Pool(8)
    for feed_url in feed_urls:
        logger.info('Queueing %s', feed_url)
        pool.apply_async(crawl, [feed_url])
    pool.close()
    pool.join()


if __name__ == '__main__':
    index.ensure()

    logging_to_console(logging.getLogger(''))
    crawl_all(sys.argv[1:] or [s['url'] for s in subscriptions()])
