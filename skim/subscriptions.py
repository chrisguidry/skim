#!/usr/bin/env python
#coding: utf-8
from datetime import datetime
import os
import sys
from xml.etree import ElementTree

from skim import scrolled
from skim.configuration import elastic, INDEX


def subscriptions():
    stats = elastic().search(index=INDEX, doc_type='entry', search_type='count', body={
        "aggs": {
            "by_feed": {
                "terms": {"field": "feed", "size": 0},
                "aggs": {
                    "first": {
                        "min": {"field": "published"}
                    },
                    "latest": {
                        "max": {"field": "published"}
                    }
                }
            }
        }
    })
    by_feed = {
        bucket['key']: (bucket['doc_count'], bucket['first']['value'], bucket['latest']['value'])
        for bucket in stats['aggregations']['by_feed']['buckets']
    }
    for subscription in scrolled(index=INDEX, doc_type='feed', sort='title.raw:asc'):
        count, first, latest = by_feed.get(subscription['url'], (0, None, None))
        subscription['entry_count'] = count
        subscription['first_entry'] = datetime.utcfromtimestamp(first/1000.0) if first else None
        subscription['latest_entry'] = datetime.utcfromtimestamp(latest/1000.0) if latest else None
        yield subscription

def by_category(category):
    search = {'filter': {'term': {'categories': category}}}
    for subscription in scrolled(index=INDEX, doc_type='feed', sort='url:asc', body=search):
        yield subscription

def subscribe(feed_url):
    elastic().update(index=INDEX, doc_type='feed', id=feed_url, body={
        'doc': {
            'url': feed_url
        },
        'doc_as_upsert': True
    })

def unsubscribe(feed_url):
    elastic().delete(index=INDEX, doc_type='feed', id=feed_url, ignore=404)

def categorize(feed_url, category):
    if not category:
        return

    elastic().update(index=INDEX, doc_type='feed', id=feed_url, body={
        'script' : '''
            if (ctx._source.categories && !ctx._source.categories.contains(category)) {
                ctx._source.categories.push(category);
            } else {
                ctx._source.categories = [category];
            }
        ''',
        'params': {
            'category': category
        },
        'upsert': {
            'url': feed_url,
            'categories': [category]
        }
    })

def opml_feeds(opml_file):
    path = []
    for event, element in ElementTree.iterparse(opml_file, events=['start', 'end']):
        if element.tag != 'outline':
            continue

        title = element.get('title')
        url = element.get('xmlUrl')

        if event == 'start' and url:
            yield os.path.join(*path) if path else '', url

        if event == 'start':
            path.append(element.get('title'))
        elif event == 'end':
            path.pop()

def import_opml(opml_filename):
    with open(opml_filename, 'r') as opml_file:
        for category, feed_url in opml_feeds(opml_file):
            subscribe(feed_url)
            categorize(feed_url, category)


if __name__ == '__main__':
    import_opml(sys.argv[1])
