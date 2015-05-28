#!/usr/bin/env python
#coding: utf-8
from datetime import datetime
import json
import os
from os.path import join
import shutil
import sys
import time

from whoosh import query, sorting

from skim import datetime_from_iso, open_file_from, slug
from skim.configuration import STORAGE_ROOT
from skim.index import query_parser, searcher
from skim.markup import to_html


def older_than(start, age):
    yield from paged(query.Every(), start, age)

def by_feed(feed_slug, start, age):
    yield from paged(query.Term('feed', feed_slug), start, age)

def search(q, start, age):
    yield from paged(query_parser.parse(q), start, age)


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

def paged(q, start, age):
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
                yield full_entry(result['feed'], result['slug'])

            if results.is_last_page():
                return

def remove_all_from_feed(feed_url):
    shutil.rmtree(join(STORAGE_ROOT, 'feeds', slug(feed_url)))
