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

def entry_filenames_by_time():
   with_times = []
   for root, _, filenames in os.walk(entries_root()):
       filenames = (os.path.join(root, filename) for filename in filenames)
       with_times += [(os.path.getmtime(filename), filename) for filename in filenames]
   return [filename for _, filename in sorted(with_times, reverse=True)]

def entry_time(path):
    return datetime.fromtimestamp(os.path.getmtime(path))

def full_entry(path):
    with open(path, 'r') as entry_file:
        return {
            'title': entry_file.readline().strip(),
            'url': entry_file.readline().strip(),
            'published': entry_time(path),
            'body': markdown.markdown(entry_file.read().strip())
        }

if __name__ == '__main__':
    for entry_filename in entry_filenames_by_time():
        print(entry_filename)
