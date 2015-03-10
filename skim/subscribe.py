#!/usr/bin/env python
#coding: utf-8
import os
import os.path
import sys
from xml.etree import ElementTree

from skim import key
from skim.configuration import STORAGE_ROOT


def subscriptions_path():
    path = os.path.join(STORAGE_ROOT, 'subscriptions')
    if not os.path.exists(path):
        os.makedirs(path)
    if not os.path.exists(os.path.join(path, 'all')):
        os.makedirs(os.path.join(path, 'all'))
    return path

def subscriptions():
    root = os.path.join(subscriptions_path(), 'all')
    for feed_filename in os.listdir(root):
        with open(os.path.join(root, feed_filename), 'r') as feed_file:
            yield feed_file.readline().strip()

def subscribe(feed_url):
    with open(os.path.join(subscriptions_path(), 'all', key(feed_url)), 'w') as feed_file:
        feed_file.write(feed_url + '\n')

def categorize(feed_url, category):
    if not category:
        return
    category_path = os.path.join(subscriptions_path(), 'categories', *os.path.split(category))
    if not os.path.exists(category_path):
        os.makedirs(category_path)
    if not os.path.exists(os.path.join(category_path, key(feed_url))):
        os.symlink(os.path.relpath(os.path.join(subscriptions_path(), 'all', key(feed_url)), category_path),
                   os.path.join(category_path, key(feed_url)))

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
