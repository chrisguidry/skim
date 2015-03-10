#!/usr/bin/env python
#coding: utf-8
from datetime import datetime
import os
import os.path
import time

import markdown

from skim import key
from skim.configuration import STORAGE_ROOT

def entries_root():
    path = os.path.join(STORAGE_ROOT, 'entries')
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def entry_filenames_by_time(through):
    through = through.isoformat()
    all_files = []
    for root, _, filenames in os.walk(entries_root()):
        all_files += [(filename, os.path.join(root, filename))
                      for filename in filenames
                      if filename >= through]
    return [fullpath for _, fullpath in sorted(all_files, reverse=True)]

def feed_entries(feed_slug):
    feed_entries_root = os.path.join(entries_root(), feed_slug)
    return [os.path.join(feed_entries_root, filename)
            for filename in sorted(os.listdir(feed_entries_root), reverse=True)]

def entry_time(path):
    return datetime.fromtimestamp(os.path.getmtime(path))

def feed(feed_key):
    with open(os.path.join(STORAGE_ROOT, 'feeds', feed_key, 'feed'), 'r') as feed_file,\
         open(os.path.join(STORAGE_ROOT, 'subscriptions', 'all', feed_key), 'r') as subscription_file:
        return {
            'url': subscription_file.readline().strip(),
            'slug': feed_key,
            'title': feed_file.readline().strip(),
            'subtitle': feed_file.readline().strip()
        }

def full_entry(path):
    md = markdown.Markdown(output_mode='html5',
                           smart_emphasis=True,
                           safe_mode='escape',
                           extensions=['markdown.extensions.abbr',
                                       'markdown.extensions.codehilite',
                                       'markdown.extensions.meta',
                                       'markdown.extensions.smart_strong',
                                       'markdown.extensions.smarty',
                                       'markdown.extensions.tables'])
    with open(path, 'r') as entry_file:
        return {
            'feed': feed(os.path.basename(os.path.dirname(path))),
            'title': entry_file.readline().strip(),
            'url': entry_file.readline().strip(),
            'published': entry_time(path),
            'body': md.convert(entry_file.read().strip())
        }


if __name__ == '__main__':
    for entry_filename in entry_filenames_by_time():
        print(entry_filename)
