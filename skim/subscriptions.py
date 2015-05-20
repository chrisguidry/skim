#coding: utf-8

from collections import defaultdict
from datetime import datetime
import os
import sys
from xml.etree import ElementTree

from skim import open_file_from, unique
from skim.configuration import STORAGE_ROOT


def subscription_urls():
    try:
        with open_file_from(STORAGE_ROOT, 'subscriptions.opml', 'r') as f:
            return list(unique(feed_url for _, feed_url in opml_feeds(f)))
    except OSError:
        return []

def subscriptions():
    raise NotImplementedError()
    # stats = elastic().search(index=INDEX, doc_type='entry', search_type='count', body={
    #     "aggs": {
    #         "by_feed": {
    #             "terms": {"field": "feed", "size": 0},
    #             "aggs": {
    #                 "first": {
    #                     "min": {"field": "published"}
    #                 },
    #                 "latest": {
    #                     "max": {"field": "published"}
    #                 }
    #             }
    #         }
    #     }
    # })
    # by_feed = {
    #     bucket['key']: (bucket['doc_count'], bucket['first']['value'], bucket['latest']['value'])
    #     for bucket in stats['aggregations']['by_feed']['buckets']
    # }
    # for subscription in scrolled(index=INDEX, doc_type='feed', sort='title.raw:asc'):
    #     count, first, latest = by_feed.get(subscription['url'], (0, None, None))
    #     subscription['entry_count'] = count
    #     subscription['first_entry'] = datetime.utcfromtimestamp(first/1000.0) if first else None
    #     subscription['latest_entry'] = datetime.utcfromtimestamp(latest/1000.0) if latest else None
    #     yield subscription

def opml_feeds(opml_file):
    path = []
    for event, element in ElementTree.iterparse(opml_file, events=['start', 'end']):
        if element.tag != 'outline':
            continue

        url = element.get('xmlUrl')

        if event == 'start' and url:
            yield os.path.join(*path) if path else '', url

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
