#!/usr/bin/env python
#coding: utf-8
from datetime import datetime
import json
import logging
import os
from os.path import join
import shutil
import sys
import time

from whoosh import query, sorting

from skim import datetime_from_iso, open_file_from, slug
from skim.configuration import STORAGE_ROOT
from skim.index import query_parser, searcher, timeseries
from skim.markup import to_html


logger = logging.getLogger(__name__)


def older_than(start, age):
    latest_query = '''
        SELECT time
        FROM timeseries
        WHERE time <= ?
        ORDER BY time DESC
        LIMIT 1;
    '''
    entries_query = '''
    SELECT  feed, entry
    FROM    timeseries
    WHERE   time > ? AND time <= ?
    ORDER BY time DESC;
    '''
    with timeseries() as ts:
        arguments = (start.isoformat() + 'Z',)
        try:
            (latest,), = ts.execute(latest_query, arguments)
        except ValueError:
            latest = start
        else:
            latest = datetime_from_iso(latest)
        arguments = ((latest - age).isoformat() + 'Z', latest.isoformat() + 'Z')
        yield from from_timeseries_cursor(ts.execute(entries_query, arguments))

def by_feed(feed_slug, start, age):
    latest_query = '''
        SELECT time
        FROM timeseries
        WHERE feed = ? AND
              time <= ?
        ORDER BY time DESC
        LIMIT 1;
    '''
    entries_query = '''
        SELECT  feed, entry
        FROM    timeseries
        WHERE   feed = ? AND
                time > ? AND time <= ?
        ORDER BY time DESC;
    '''
    with timeseries() as ts:
        arguments = (feed_slug, start.isoformat() + 'Z')
        try:
            (latest,), = ts.execute(latest_query, arguments)
        except ValueError:
            latest = start
        else:
            latest = datetime_from_iso(latest)
        arguments = (feed_slug, (latest - age).isoformat() + 'Z', latest.isoformat() + 'Z')
        yield from from_timeseries_cursor(ts.execute(entries_query, arguments))

def search(q, start, age):
    yield from paged_search(query_parser.parse(q), start, age)


def full_entry(feed_slug, entry_slug):
    feed_dir = join(STORAGE_ROOT, 'feeds', feed_slug)
    entry_dir = join(feed_dir, entry_slug)

    with open_file_from(feed_dir, 'feed.json', 'r') as feed_file, \
         open_file_from(entry_dir, 'entry.json', 'r') as entry_file, \
         open_file_from(entry_dir, 'entry.html', 'r') as entry_html:

        entry = json.load(entry_file)
        entry['published'] = datetime_from_iso(entry['published'])
        entry['feed'] = json.load(feed_file)
        entry['feed']['slug'] = feed_slug
        entry['body'] = entry_html.read()
        return entry

def newest_before(searcher, q, start):
    results = searcher.search(q,
                              filter=query.DateRange('published', None, start),
                              sortedby=sorting.FieldFacet('slug', reverse=True),
                              limit=1)
    if not len(results):
        return None
    return results[0]['published']

def from_timeseries_cursor(cursor):
    for feed_slug, entry_slug in cursor:
        try:
            yield full_entry(feed_slug, entry_slug)
        except IOError:
            logger.exception('Error reading %s %s', result['feed'], result['slug'])


def paged_search(q, start, age):
    with searcher() as s:
        start = newest_before(s, q, start)
        if not start:
            return

        for i in range(1, sys.maxsize):
            results = s.search_page(
                q,
                i, pagelen=250,
                filter=query.DateRange('published', start - age, start),
                sortedby=sorting.FieldFacet('slug', reverse=True) # note sorting by date seemed to be broken
            )
            for result in results:
                if result['published'] > start:
                    continue
                if result['published'] < (start - age):
                    return

                try:
                    yield full_entry(result['feed'], result['slug'])
                except IOError:
                    logger.exception('Error reading %s %s', result['feed'], result['slug'])

            if results.is_last_page():
                return

def remove_all_from_feed(feed_url):
    feed_slug = slug(feed_url)
    shutil.rmtree(join(STORAGE_ROOT, 'feeds', feed_slug))
    with timeseries() as ts:
        ts.execute('DELETE FROM timeseries WHERE feed = ?', [feed_slug])

PER_FEED_RETENTION = 250
def enforce_retention():
    feeds_to_clean_query = '''
        SELECT feed
        FROM   timeseries
        GROUP BY feed
        HAVING count(*) > ?;
    '''

    entries_to_nuke_query = '''
    SELECT  entry
    FROM    timeseries
    WHERE   feed = ?
    ORDER BY time DESC
    LIMIT 4294967296 OFFSET ?;
    '''

    delete_entry_query = 'DELETE FROM timeseries WHERE feed = ? AND entry = ?;'

    logger.info('Enforcing retention...')
    with timeseries() as ts:
        for feed_slug in ts.execute(feeds_to_clean_query, [PER_FEED_RETENTION]):
            logger.info('Enforcing retention on %r', feed_slug)
            arguments = [feed, PER_FEED_RETENTION]
            feed_root = join(STORAGE_ROOT, 'feeds', feed_slug)
            for entry in ts.execute(entries_to_nuke_query, arguments):
                entry_root = join(feed_root, entry)
                logger.info('Removing entry %r', entry_root)
                shutil.rmtree(entry_root)
                ts.execute(delete_entry_query, [feed, entry])
    logger.info('Finished enforcing retention.')
