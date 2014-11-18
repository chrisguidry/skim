#!/usr/bin/env python
# coding: utf-8
import os
import os.path
import sys

from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, ID, TEXT, DATETIME
from whoosh.qparser import QueryParser
from whoosh.sorting import FieldFacet

from skim.configuration import STORAGE_ROOT


def search_index():
    path = os.path.join(STORAGE_ROOT, 'index')
    if exists_in(path, indexname='entries'):
        return open_dir(path, indexname='entries')

    os.makedirs(path)
    schema = Schema(feed_title=TEXT(stored=True),
                    feed_path=ID(stored=True),
                    path=ID(unique=True, stored=True),
                    title=TEXT(stored=True),
                    published=DATETIME(stored=True, sortable=True),
                    content=TEXT)
    return create_in(path, schema, indexname='entries')

def search(query, limit=200):
    index = search_index()
    with index.searcher() as searcher:
        query = QueryParser('content', index.schema).parse(query)
        results = searcher.search(query, limit=limit, sortedby=FieldFacet('published', reverse=True))
        for result in results:
            yield result


if __name__ == '__main__':
    query = ' '.join(sys.argv[1:]) or '*'
    for result in search(query):
        print(dir(result))
        print(result.keys())
        print(result)
