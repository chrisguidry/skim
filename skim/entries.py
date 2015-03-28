#!/usr/bin/env python
#coding: utf-8
from datetime import datetime
import os
import os.path
import time

from skim import scrolled, subscriptions
from skim.configuration import elastic, INDEX
from skim.markup import to_html


def feed_cache():
    return {feed['url']: feed for feed in scrolled(index=INDEX, doc_type='feed')}

def search(query):
    yield from full_entries(scrolled(index=INDEX, doc_type='entry', sort='published:desc', body={
        'query': {
            'query_string': {
                'query': query
            }
        }
    }))

def since(since):
    yield from full_entries(scrolled(index=INDEX, doc_type='entry', sort='published:desc', body={
        'filter': {
            'range' : {'published' : {'gte' : since}}
        }
    }))

def by_feed(feed_url):
    yield from full_entries(scrolled(index=INDEX, doc_type='entry', sort='published:desc', body={
        'filter': {
            'term': {'feed': feed_url}
        }
    }))

def by_category(category):
    feed_urls = [feed['url'] for feed in subscriptions.by_category(category)]
    yield from full_entries(scrolled(index=INDEX, doc_type='entry', sort='published:desc', body={
        'filter': {
            'terms': {'feed': feed_urls}
        }
    }))

def interesting(since):
    results = elastic().search(index=INDEX, doc_type='entry', body={
        'query': {
            'filtered': {
                'filter': {
                    'range': {
                        'published': {'gte': since.isoformat() + 'Z'}
                    }
                }
            }
        },
        'aggs': {
            'most_sig': {
                'significant_terms': {
                    'field': 'title',
                    'size': 20
                }
            }
        }
    })
    for bucket in results['aggregations']['most_sig']['buckets']:
        yield from full_entries(scrolled(index=INDEX, doc_type='entry', body={
            'query': {
                'filtered': {
                    'query': {
                        'match': {'title': bucket['key']}
                    },
                    'filter': {
                        'range': {'published': {'gte': since.isoformat() + 'Z'}}
                    }
                }
            }
        }))

def datetime_from_iso(string):
    if not string:
        return None

    for format in ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ']:
        try:
            return datetime.strptime(string, format)
        except ValueError:
            pass

    return None

def full_entries(entries):
    feeds = feed_cache()
    for entry in entries:
        entry['title'] = entry['title']
        entry['body'] = to_html(entry['text'])
        entry['feed'] = feeds[entry['feed']]
        entry['published'] = datetime_from_iso(entry['published'])
        yield entry


def remove_all_from_feed(feed_url):
    es = elastic()
    search = {
        'filter': {
            'term': {'feed': feed_url}
        }
    }
    for entry in scrolled(index=INDEX, doc_type='entry', sort='published:desc', body=search):
        es.delete(index=INDEX, doc_type='entry', id=entry['url'])
