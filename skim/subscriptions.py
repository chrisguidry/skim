#coding: utf-8

from collections import defaultdict
from datetime import datetime
import os
from os.path import exists, join
import sys
from xml.etree import ElementTree

from skim import datetime_from_iso, open_file_from, slug, unique
from skim.configuration import STORAGE_ROOT


def subscription_urls():
    try:
        with open_file_from(STORAGE_ROOT, 'subscriptions.opml', 'r') as f:
            return list(unique(feed_url for _, _, feed_url in opml_feeds(f)))
    except OSError:
        return []

def feed_stats(feed_url):
    try:
        listing = os.listdir(join(STORAGE_ROOT, 'feeds', slug(feed_url)))
    except OSError:
        listing = []

    listing = listing[:-3]

    if not listing:
        return 0, None, None

    return len(listing), date_from_entry_slug(listing[0]), date_from_entry_slug(listing[-1])

def date_from_entry_slug(entry_slug):
    if entry_slug[19] == '.':
        date_part = entry_slug[:26]
    else:
        date_part = entry_slug[:19]
    return datetime_from_iso(date_part + 'Z')

def subscriptions():
    by_url = {}
    try:
        with open_file_from(STORAGE_ROOT, 'subscriptions.opml', 'r') as f:
            for category, title, feed_url in opml_feeds(f):
                if feed_url not in by_url:
                    by_url[feed_url] = {
                        'url': feed_url,
                        'slug': slug(feed_url),
                        'title': title,
                        'categories': []
                    }

                    entry_count, first_entry, latest_entry = feed_stats(feed_url)
                    by_url[feed_url].update({
                        'entry_count': entry_count,
                        'first_entry': first_entry,
                        'latest_entry': latest_entry
                    })
                by_url[feed_url]['categories'].append(category)
        return sorted(by_url.values(), key=lambda s: s['slug'])
    except OSError:
        return []

def opml_feeds(opml_file):
    path = []
    for event, element in ElementTree.iterparse(opml_file, events=['start', 'end']):
        if element.tag != 'outline':
            continue

        title = element.get('text')
        url = element.get('xmlUrl')

        if event == 'start' and url:
            yield os.path.join(*path) if path else '', title or url, url

        if event == 'start':
            path.append(element.get('text'))
        elif event == 'end':
            path.pop()

def by_category(category):
    raise NotImplementedError()
    search = {'filter': {'term': {'categories': category}}}
    for subscription in scrolled(index=INDEX, doc_type='feed', sort='url:asc', body=search):
        yield subscription

def subscribe(feed_url):
    raise NotImplementedError()
    elastic().update(index=INDEX, doc_type='feed', id=feed_url, body={
        'script' : '''
            if (!ctx._source.title) {
                ctx._source.title = feed_url
            }
        ''',
        'params': {
            'feed_url': feed_url
        },
        'upsert': {
            'url': feed_url,
            'title': feed_url
        }
    })

def unsubscribe(feed_url):
    raise NotImplementedError()
    elastic().delete(index=INDEX, doc_type='feed', id=feed_url, ignore=404)

def categorize(feed_url, category):
    if not category:
        return

    raise NotImplementedError()
    # elastic().update(index=INDEX, doc_type='feed', id=feed_url, body={
    #     'script' : '''
    #         if (ctx._source.categories && !ctx._source.categories.contains(category)) {
    #             ctx._source.categories.push(category);
    #         } else {
    #             ctx._source.categories = [category];
    #         }
    #     ''',
    #     'params': {
    #         'category': category
    #     },
    #     'upsert': {
    #         'url': feed_url,
    #         'categories': [category]
    #     }
    # })

def import_opml(opml_filename):
    raise NotImplementedError()
    with open(opml_filename, 'r') as opml_file:
        for category, feed_url in opml_feeds(opml_file):
            subscribe(feed_url)
            categorize(feed_url, category)
