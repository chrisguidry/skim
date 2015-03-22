#!/usr/bin/env python
#coding: utf-8
from datetime import datetime
import os
import os.path
import time

import markdown

from skim import key
from skim.configuration import elastic, INDEX


def scrolled(*args, **kwargs):
    es = elastic()
    kwargs['scroll'] = kwargs.get('scroll') or '10s'
    results = es.search(*args, **kwargs)
    while results['hits']['hits']:
        for hit in results['hits']['hits']:
            yield hit['_source']
        results = es.scroll(scroll_id=results['_scroll_id'], scroll=kwargs['scroll'])

def feed_cache():
    return {feed['url']: feed for feed in scrolled(index=INDEX, doc_type='feed')}

def search(query):
    search = {
        'query': {
            'query_string': {
                'query': query
            }
        }
    }
    feeds = feed_cache()
    for entry in scrolled(index=INDEX, doc_type='entry', sort='published:desc', body=search):
        yield full_entry(feeds, entry)

def since(since):
    search = {
        'filter': {
            'range' : {'published' : {'gte' : since}}
        }
    }
    feeds = feed_cache()
    for entry in scrolled(index=INDEX, doc_type='entry', sort='published:desc', body=search):
        yield full_entry(feeds, entry)

def by_feed(feed_url):
    search = {
        'filter': {
            'term': {'feed': feed_url}
        }
    }
    feeds = feed_cache()
    for entry in scrolled(index=INDEX, doc_type='entry', sort='published:desc', body=search):
        yield full_entry(feeds, entry)

def interesting(since):
    search = {
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
    }

    feeds = feed_cache()
    results = elastic().search(index=INDEX, doc_type='entry', body=search)
    for bucket in results['aggregations']['most_sig']['buckets']:
        search = {
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
        }
        for entry in scrolled(index=INDEX, doc_type='entry', body=search):
            yield full_entry(feeds, entry)

def datetime_from_iso(string):
    if not string:
        return None

    for format in ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ']:
        try:
            return datetime.strptime(string, format)
        except ValueError:
            pass

    return None

def full_entry(feeds, entry):
    md = markdown.Markdown(output_mode='html5',
                           smart_emphasis=True,
                           safe_mode='escape',
                           extensions=['markdown.extensions.abbr',
                                       'markdown.extensions.codehilite',
                                       'markdown.extensions.meta',
                                       'markdown.extensions.smart_strong',
                                       'markdown.extensions.smarty',
                                       'markdown.extensions.tables'])

    entry['feed'] = feeds[entry['feed']]
    entry['body'] = md.convert(entry['text'])
    entry['published'] = datetime_from_iso(entry['published'])
    return entry
