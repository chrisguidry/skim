# coding: utf-8

import os
from os.path import isdir, join

from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, DATETIME, ID, KEYWORD, TEXT
from whoosh.qparser import QueryParser
from whoosh.writing import AsyncWriter, BufferedWriter

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
