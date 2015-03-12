#!/usr/bin/env python
#coding: utf-8
from datetime import datetime, timezone
import dbm
import logging
from multiprocessing import Process, Queue
import os
import os.path
import sys
import time

import feedparser
import html2text
from slugify import slugify

from skim import __version__, key, logging_to_console
from skim.configuration import STORAGE_ROOT
from skim.entries import entries_root
from skim.search import search_index
from skim.subscribe import subscriptions

feedparser.USER_AGENT = 'Skim/{} +https://github.com/chrisguidry/skim/'.format(__version__)
html2text.config.UNICODE_SNOB = 1
html2text.config.SINGLE_LINE_BREAK = False
HTML2TEXT_CONFIG = {'bodywidth': 0}

logger = logging.getLogger(__name__)


def feed_path(feed_url):
    path = os.path.join(STORAGE_ROOT, 'feeds', key(feed_url))
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def entries_path(feed_url):
    path = os.path.join(entries_root(), key(feed_url))
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def entry_filename(feed_url, entry):
    basename = '{}-{}'.format(entry_time(entry).isoformat(), slugify(entry_title(entry))[:100])
    return os.path.join(entries_path(feed_url), basename)

def url_index_file(feed_url):
    return os.path.join(feed_path(feed_url), 'url_index.db')

def conditional_get_state(feed_url):
    state_filename = os.path.join(feed_path(feed_url), 'conditional')
    if not os.path.exists(state_filename):
        return None, None
    with open(state_filename, 'r') as state_file:
        etag, modified, *_ = [line.strip() for line in state_file.readlines()]
    return etag or None, modified or None

def save_conditional_get_state(feed_url, etag, modified):
    with open(os.path.join(feed_path(feed_url), 'conditional'), 'w') as state_file:
        state_file.write((etag or '') + '\n')
        state_file.write((modified or '') + '\n')

def save_headers(feed_url, headers):
    with open(os.path.join(feed_path(feed_url), 'headers'), 'w') as headers_file:
        for key, value in headers.items():
            headers_file.write('{}: {}\n'.format(key, value))

def save_feed(feed_url, feed):
    with open(os.path.join(feed_path(feed_url), 'feed'), 'w') as feed_file:
        feed_file.write(feed.get('title', feed_url) + '\n')
        feed_file.write(feed.get('subtitle', '') + '\n')

def save_entry(feed_url, feed, entry):
    filename = entry_filename(feed_url, entry)
    with open(filename, 'w') as entry_file:
        entry_file.write('url: {}\n'.format(entry.get('link', '')))
        entry_file.write('title: {}\n'.format(entry_title(entry)))
        entry_file.write('published: {}\n'.format(entry_time(entry).isoformat() + 'Z'))
        entry_file.write('\n')
        entry_file.write(entry_text(entry))

    os.utime(filename,
             times=(time.mktime(time.gmtime()),
                    time.mktime(entry_time(entry).utctimetuple())))
    return filename

def entry_url(feed_url, entry):
    return entry.get('link') or '{}#{}'.format(feed_url, entry_time(entry).isoformat())

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

def crawl(feed_url, indexing_queue):
    logger.info('Crawling %r...', feed_url)
    etag, modified = conditional_get_state(feed_url)
    parsed = feedparser.parse(feed_url, etag=etag, modified=modified)
    if not parsed.get('status'):
        logger.warn('No status returned while crawling %s.  Parsed: %r', feed_url, parsed)
        return

    if parsed.status == 304:
        return

    save_headers(feed_url, parsed.headers)
    if parsed.status not in (200, 301, 302):
        logger.warn('Status %s while crawling %s.', parsed.status, feed_url)
        return

    save_feed(feed_url, parsed.feed)

    with dbm.open(url_index_file(feed_url), 'c') as url_index:
        for entry in parsed.entries:
            new_entry_url = entry_url(feed_url, entry)
            entry_key = new_entry_url.encode('utf-8')
            if entry_key in url_index:
                logger.info('%s has already been seen on %s', new_entry_url, feed_url)
                continue

            logger.info('New entry %s on %s', new_entry_url, feed_url)

            entry_full_path = save_entry(feed_url, parsed.feed, entry)
            indexing_queue.put((feed_url, parsed.feed, entry, entry_full_path), block=True)

            url_index[entry_key] = '1'

    save_conditional_get_state(feed_url, parsed.get('etag'), parsed.get('modified'))


def crawler(crawl_queue, indexing_queue):
    logger.info('Starting crawler...')
    while True:
        feed_url = crawl_queue.get(block=True)
        if feed_url is None:
            break

        try:
            crawl(feed_url, indexing_queue)
        except Exception:
            logger.error('Error crawling %r', feed_url, exc_info=True)

    indexing_queue.put((None, None, None, None), block=True)

def indexer(indexing_queue, expected_to_finish):
    logger.info('Starting indexer...')
    index = search_index()
    writer = index.writer()
    indexed = 0
    while True:
        feed_url, feed, entry, filename = indexing_queue.get(block=True)
        if entry is None:
            expected_to_finish -= 1
            if expected_to_finish == 0:
                break
            else:
                continue

        logger.info('Indexing %r', entry_url(feed_url, entry))
        writer.update_document(feed_path=os.path.relpath(feed_path(feed_url), STORAGE_ROOT),
                               feed_title=feed.title,
                               path=os.path.relpath(filename, STORAGE_ROOT),
                               title=entry_title(entry),
                               published=entry_time(entry),
                               content=entry_text(entry))

        indexed += 1
        if indexed % 100 == 0:
            logger.info('Committing index...')
            writer.commit()
            writer = index.writer()

    logger.info('Final index commit.')
    writer.commit()

def crawl_all(feed_urls=subscriptions):
    CRAWLERS = 8
    crawl_queue = Queue()
    indexing_queue = Queue()

    processes = [Process(target=crawler, args=(crawl_queue, indexing_queue,), name='crawler-%s' % i)
                 for i in range(CRAWLERS)]
    processes.append(Process(target=indexer, args=(indexing_queue, CRAWLERS), name='indexer'))

    for process in processes:
        process.start()

    for feed_url in feed_urls():
        logger.info('Queueing %s', feed_url)
        crawl_queue.put(feed_url, block=True)

    for _ in range(CRAWLERS):
        crawl_queue.put(None, block=True)

    try:
        for process in processes:
            process.join()
    except:
        for process in processes:
            process.terminate()
    finally:
        for process in processes:
            process.join()


if __name__ == '__main__':
    logging_to_console(logging.getLogger(''))
    if len(sys.argv) > 1:
        crawl_all(lambda: sys.argv[1:])
    else:
        crawl_all()
