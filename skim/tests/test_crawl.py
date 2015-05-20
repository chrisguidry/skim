#coding: utf-8

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


@httpretty.activate
def test_crawl_basic_file_structure(storage):
    httpretty.register_uri(httpretty.GET,
                           'http://example.com/feed',
                           body=BASIC_FEED,
                           content_type='application/rss+xml')

    crawl.crawl('http://example.com/feed')

    assert isdir(storage)
    assert isdir(join(storage, 'feeds'))

    feed_dir = join(storage, 'feeds', 'http-com-example-feed')
    assert isdir(feed_dir)

    assert isdir(join(feed_dir, '2015-05-10T00:00:00-http-com-example-entry-1'))
    assert isdir(join(feed_dir, '2015-05-11T00:00:00-http-com-example-entry-2'))

    entry_dir = join(feed_dir, '2015-05-10T00:00:00-http-com-example-entry-1')
    assert isfile(join(entry_dir, 'entry.json'))
