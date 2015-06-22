# coding: utf-8

from contextlib import contextmanager
import os
from os.path import isdir, isfile, join
import sqlite3

from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, DATETIME, ID, KEYWORD, TEXT
from whoosh.qparser import QueryParser
from whoosh.writing import AsyncWriter, BufferedWriter

from skim import slug
from skim.configuration import STORAGE_ROOT


schema = Schema(
    feed=ID(stored=True),
    slug=ID(stored=True),
    published=DATETIME(stored=True, sortable=True),
    title=TEXT(),
    text=TEXT(),
    authors=TEXT(),
    tags=KEYWORD(lowercase=True, commas=True)
)

query_parser = QueryParser('text', schema=schema)

def ensure_index():
    index_dir = join(STORAGE_ROOT, 'index')
    if not isdir(index_dir):
        os.makedirs(index_dir)
        return create_in(index_dir, schema)
    return open_dir(index_dir)

def searcher():
    return ensure_index().searcher()

def async_writer():
    return AsyncWriter(ensure_index())

def buffered_writer():
    return BufferedWriter(ensure_index())

def index_writer():
    return ensure_index().writer()


@contextmanager
def timeseries():
    index_filename = join(STORAGE_ROOT, 'timeseries.sqlite3')
    with sqlite3.connect(index_filename) as c:
        yield c

def ensure_timeseries():
    index_filename = join(STORAGE_ROOT, 'timeseries.sqlite3')
    if not isfile(index_filename):
        with timeseries() as ts:
            ts.execute('''
            CREATE TABLE IF NOT EXISTS timeseries (
                feed TEXT NOT NULL,
                entry TEXT NOT NULL,
                time TEXT NOT NULL
            );''')
            ts.execute('CREATE UNIQUE INDEX IF NOT EXISTS timeseries_all ON timeseries (time, feed, entry);')
            ts.execute('CREATE INDEX IF NOT EXISTS timeseries_time ON timeseries (time);')
            ts.execute('CREATE INDEX IF NOT EXISTS timeseries_time_feed ON timeseries (time, feed);')

def add_to_timeseries(feed_slug, entry_slug, entry_time):
    with timeseries() as ts:
        ts.execute('INSERT INTO timeseries(feed, entry, time) VALUES (?, ?, ?)',
                   (feed_slug, entry_slug, entry_time.isoformat() + 'Z'))
