#!/usr/bin/env python
#coding: utf-8
import os
import sys
from xml.etree import ElementTree

from skim import key
from skim.configuration import elastic, INDEX


def subscriptions():
    es = elastic()
    results = es.search(index=INDEX, doc_type='subscription', sort='url:asc', scroll='10s')
    while results['hits']['hits']:
        for hit in results['hits']['hits']:
            yield hit['_source']
        results = es.scroll(scroll_id=results['_scroll_id'], scroll='10s')

def subscribe(feed_url):
    elastic().update(index=INDEX, doc_type='subscription', id=feed_url, body={
        'doc': {
            'url': feed_url,
            'categories': []
        },
        'doc_as_upsert': True
    })

def categorize(feed_url, category):
    if not category:
        return

    elastic().update(index=INDEX, doc_type='subscription', id=feed_url, body={
        'script' : 'ctx._source.categories.push(category)',
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
