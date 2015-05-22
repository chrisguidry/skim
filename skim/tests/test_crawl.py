#coding: utf-8

import dbm
import os
from os.path import isdir, isfile, join
import shutil
import tempfile

import httpretty
import mock
import pytest

from skim import configuration, crawl


BASIC_FEED = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
    <channel>
        <title>Example Feed</title>
        <link>http://example.com/feed</link>
        <description>A great little feed</description>
        <item>
            <title>Entry Two</title>
            <link>http://example.com/entry-2</link>
            <description>The second entry</description>
            <pubDate>Sun, 11 May 2015 00:00:00 GMT</pubDate>
        </item>
        <item>
            <title>Entry One</title>
            <link>http://example.com/entry-1</link>
            <description>The first entry</description>
            <pubDate>Sun, 10 May 2015 00:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>
"""

@pytest.fixture
def storage(request):
    original_storage = configuration.STORAGE_ROOT
    storage = tempfile.mkdtemp()
    configuration.STORAGE_ROOT = crawl.STORAGE_ROOT = storage
    def cleanup():
        shutil.rmtree(storage)
        configuration.STORAGE_ROOT = crawl.STORAGE_ROOT = original_storage
    request.addfinalizer(cleanup)
    return storage

@pytest.fixture
def simple_feed(request):
    feed_url = 'http://example.com/feed'
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, feed_url,
        responses=[
            httpretty.Response(status=200,
                               body=BASIC_FEED,
                               content_type='application/rss+xml',
                               adding_headers={
                                'Etag': 'the-etag',
                                'Last-Modified': 'the date'
                               }),
            httpretty.Response(status=304,
                               body='',
                               content_type='application/rss+xml',
                               adding_headers={
                                'Etag': 'the-etag',
                                'Last-Modified': 'the date'
                               })
        ]
    )
    request.addfinalizer(httpretty.disable)
    return feed_url


def test_crawl_basic_file_structure(storage, simple_feed):
    crawl.crawl(simple_feed)

    assert isdir(storage)
    assert isdir(join(storage, 'feeds'))

    feed_dir = join(storage, 'feeds', 'http-com-example-feed')
    assert isdir(feed_dir)

    assert isfile(join(feed_dir, 'conditional-get'))
    assert isfile(join(feed_dir, 'entries.db'))

    assert isdir(join(feed_dir, '2015-05-10T00:00:00-http-com-example-entry-1'))
    assert isdir(join(feed_dir, '2015-05-11T00:00:00-http-com-example-entry-2'))

    entry_dir = join(feed_dir, '2015-05-10T00:00:00-http-com-example-entry-1')
    assert isfile(join(entry_dir, 'entry.json'))

def test_crawl_basic_bookkeeping(storage, simple_feed):
    crawl.crawl(simple_feed)

    feed_dir = join(storage, 'feeds', 'http-com-example-feed')
    with open(join(feed_dir, 'conditional-get')) as conditional_get_state:
        assert 'the-etag\nthe date\n' == conditional_get_state.read()

    with dbm.open(join(feed_dir, 'entries.db')) as entry_url_db:
        assert 'http://example.com/entry-1' in entry_url_db
        assert 'http://example.com/entry-2' in entry_url_db

def test_crawl_conditional_get_restore(storage, simple_feed):
    crawl.crawl(simple_feed)
    with mock.patch('skim.crawl.save_feed', side_effect=Exception):
        # it should not attempt to save anything in the case of a 304
        crawl.crawl(simple_feed)
