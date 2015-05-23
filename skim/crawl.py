# coding: utf-8

from contextlib import contextmanager
from datetime import datetime, timezone
import dbm
import json
import logging
from multiprocessing.pool import ThreadPool
import os
from os.path import join
import re
import sys
import time

import feedparser

from skim import __version__, open_file_from, slug, unique
from skim.configuration import STORAGE_ROOT
from skim.index import async_writer, buffered_writer
from skim.markup import remove_tags, to_html, to_text
from skim.subscriptions import subscription_urls

feedparser.USER_AGENT = 'Skim/{} +https://github.com/chrisguidry/skim/'.format(__version__)

logger = logging.getLogger(__name__)


def feed_directory(feed_url):
    return join(STORAGE_ROOT, 'feeds', slug(feed_url))

@contextmanager
def feed_file(feed_url, filename, mode):
    with open_file_from(feed_directory(feed_url), filename, mode) as f:
        yield f

@contextmanager
def entry_urls(feed_url):
    with dbm.open(join(feed_directory(feed_url), 'entries.db'), 'c') as entry_url_db:
        yield entry_url_db

def entry_slug(feed_url, entry):
    timestamp = entry_time(entry).isoformat() + 'Z'
    entry_slug = slug(entry_url(feed_url, entry))
    directory_name = '-'.join([timestamp, entry_slug])[:255]
    return directory_name

def entry_directory(feed_url, entry):
    return join(STORAGE_ROOT, 'feeds', slug(feed_url), entry_slug(feed_url, entry))

@contextmanager
def entry_file(feed_url, entry, filename, mode):
    with open_file_from(entry_directory(feed_url, entry), filename, mode) as f:
        yield f

def conditional_get_state(feed_url):
    try:
        with feed_file(feed_url, 'conditional-get', 'r') as f:
            etag, modified = [line.strip() for line in f.readlines()]
            return etag or None, modified or None
    except (OSError, ValueError):
        pass
    return None, None

def save_conditional_get_state(feed_url, etag, modified):
    with feed_file(feed_url, 'conditional-get', 'w') as f:
        f.write((etag or '') + '\n')
        f.write((modified or '') + '\n')

def save_feed(feed_url, feed):
    with feed_file(feed_url, 'feed.json', 'w') as f:
        json.dump({
            'url': feed_url,
            'title': feed.get('title', feed_url),
            'subtitle': feed.get('subtitle'),
            'authors': author_names(feed),
            'publisher': feed.get('publisher_detail', {}).get('name'),
            'tags': tags(feed),
            'icon': feed.get('icon'),
            'image': feed.get('image', {}).get('href') or feed.get('logo')
        }, f, indent=4)

def save_entry(feed_url, entry):
    text = entry_text(entry)
    try:
        html = to_html(text)
    except Exception:
        logger.exception('Error extracting HTML of entry %s', entry_url(feed_url, entry))
        html = ''

    with entry_file(feed_url, entry, 'entry.json', 'w') as f:
        json.dump({
            'url': entry_link(entry),
            'title': entry_title(entry),
            'published': entry_time(entry).isoformat() + 'Z',
            'image': entry.get('image', {}).get('href'),
            'authors': author_names(entry),
            'tags': tags(entry),
            'enclosures': [{'type': enc.get('type', ''), 'url': enc.get('href')}
                           for enc in entry.get('enclosures') or []]
        }, f, indent=4)

    with entry_file(feed_url, entry, 'entry.md', 'w') as f:
        f.write(text)

    with entry_file(feed_url, entry, 'entry.html', 'w') as f:
        f.write(html)

def index_entry(feed_url, entry, writer):
    writer.add_document(**{
        'feed': slug(feed_url),
        'slug': entry_slug(feed_url, entry),
        'title': entry_title(entry),
        'published': entry_time(entry),
        'text': entry_text(entry),
        'authors': ' '.join(author_names(entry)),
        'tags': ','.join(tags(entry)),
    })

def author_names(feed_or_entry):
    return list(unique(remove_tags(author.name)
                       for author in authors(feed_or_entry)
                       if author.get('name')))

def authors(feed_or_entry):
    if feed_or_entry.get('author_detail'):
        yield feed_or_entry['author_detail']
    for contributor in feed_or_entry.get('contributors', []):
        yield contributor

def tags(feed_or_entry):
    return list(unique(tag.label or tag.term
                       for tag in feed_or_entry.get('tags', [])))

def entry_url(feed_url, entry):
    return entry_link(entry) or '{}#{}'.format(feed_url, entry_time(entry).isoformat() + 'Z')

def entry_link(entry):
    for enclosure in entry.get('enclosures', []):
        if enclosure.get('type', '').startswith(('audio/', 'video/')) and enclosure.get('href'):
            return enclosure['href']
    return entry.get('link')

def entry_title(entry):
    title = entry.get('title')
    if not title:
        return '[untitled]'
    return to_text(None, None, title)

def entry_time(entry):
    try:
        return entry['__timestamp__']
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

    entry['__timestamp__'] = entry_time

    return entry_time

def guess_time_from_url(url):
    match = re.search('((?P<year>2(\d{3}))/(?P<month>\d{1,2})(/(?P<day>\d{1,2}))?)', url)
    if match:
        try:
            return datetime(int(match.group('year')), int(match.group('month')), int(match.group('day') or '1'))
        except ValueError:
            return None

def entry_text(entry):
    content = ''
    if 'content' in entry:
        content = entry.content[0]
    elif 'summary_detail' in entry:
        content = entry.summary_detail
    else:
        return ''

    return to_text(content.base, entry_link(entry), content.value)


def crawl(feed_url, writer):
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

    with entry_urls(feed_url) as entry_url_db:
        for entry in parsed.entries:
            new_entry_url = entry_url(feed_url, entry)
            if new_entry_url.encode('utf-8') in entry_url_db:
                logger.info('%s has already been seen', new_entry_url)
                continue

            logger.info('New entry %s on %s', new_entry_url, feed_url)
            entry_url_db[new_entry_url] = entry_time(entry).isoformat() + 'Z'
            save_entry(feed_url, entry)
            index_entry(feed_url, entry, writer)

    save_conditional_get_state(feed_url, parsed.get('etag'), parsed.get('modified'))

def crawl_all(feed_urls, wait=True):
    if wait:
        writer = buffered_writer()
    else:
        writer = async_writer()

    pool = ThreadPool(8)
    results = []
    for feed_url in feed_urls:
        logger.info('Queueing %s', feed_url)
        results.append(pool.apply_async(crawl, [feed_url, writer]))
    pool.close()

    if not wait:
        return

    for index, result in enumerate(results):
        result.get()
        logger.info('Finished crawling %s/%s', index+1, len(feed_urls))
    writer.close()
    pool.join()

def recrawl(feed_url):
    from skim.entries import remove_all_from_feed
    remove_all_from_feed(feed_url)
    save_conditional_get_state(feed_url, None, None)
    crawl(feed_url)


if __name__ == '__main__':
    crawl_all(sys.argv[1:] or subscription_urls())
