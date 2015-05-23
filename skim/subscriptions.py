#coding: utf-8

from collections import defaultdict
from datetime import datetime
import os
from os.path import exists, join
import sys
from lxml.etree import Element, ElementTree, fromstring, iterparse, parse

from skim import datetime_from_iso, open_file_from, slug, unique
from skim.configuration import STORAGE_ROOT


def subscriptions():
    by_url = {}
    try:
        with open_file_from(STORAGE_ROOT, 'subscriptions.opml', 'rb') as f:
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

def subscription_urls():
    try:
        with open_file_from(STORAGE_ROOT, 'subscriptions.opml', 'rb') as f:
            return list(unique(feed_url for _, _, feed_url in opml_feeds(f)))
    except OSError:
        return []


def opml_feeds(opml_file):
    path = []
    for event, element in iterparse(opml_file, events=['start', 'end']):
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


EMPTY_OPML = """<?xml version="1.0"?>
<opml version="1.0">
    <head></head>
    <body></body>
</opml>
"""

def subscription_tree():
    try:
        tree = parse(join(STORAGE_ROOT, 'subscriptions.opml'))
    except OSError:
        tree = fromstring(EMPTY_OPML)

    root = tree.getroot()
    return tree, root, root.find('head'), root.find('body')

def save_subscription_tree(tree):
    tree.write(join(STORAGE_ROOT, 'subscriptions.opml'))

def subscribe(feed_url):
    tree, _, _, body = subscription_tree()
    for outline in body.findall('.//outline'):
        if outline.get('xmlUrl') == feed_url:
            return

    subscription = Element('outline')
    subscription.set('text', feed_url)
    subscription.set('xmlUrl', feed_url)
    body.append(subscription)

    save_subscription_tree(tree)

def unsubscribe(feed_url):
    tree, _, _, body = subscription_tree()
    for outline in body.findall('.//outline'):
        if outline.get('xmlUrl') == feed_url:
            outline.getparent().remove(outline)

    save_subscription_tree(tree)
