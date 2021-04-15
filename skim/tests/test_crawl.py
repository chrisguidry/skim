from unittest import mock

import pytest
from aioresponses import aioresponses

from skim import crawl, subscriptions


@pytest.fixture
async def one_subscription(skim_db):
    await subscriptions.add('https://example.com/1')


@pytest.fixture
async def two_subscriptions(one_subscription):
    await subscriptions.add('https://example.com/2')


async def test_crawl(two_subscriptions):
    with mock.patch('skim.crawl.fetch') as fetch:
        fetch.side_effect = [
            ('https://example.com/1', {'title': 'One'}, [{'the': 'entry'}]),
            ('https://example.com/2', {'title': 'Two'}, [{'the': 'entry'}])
        ]

        await crawl.crawl()

        fetch.assert_has_calls([
            mock.call('https://example.com/1'),
            mock.call('https://example.com/2')
        ])

        by_feed = {s['feed']: s async for s in subscriptions.all()}

        assert by_feed == {
            'https://example.com/1': {
                'feed': 'https://example.com/1',
                'title': 'One',
                'site': None,
                'icon': None,
            },
            'https://example.com/2': {
                'feed': 'https://example.com/2',
                'title': 'Two',
                'site': None,
                'icon': None,
            }
        }


async def test_crawl_fetch_errors(one_subscription):
    with mock.patch('skim.crawl.fetch') as fetch:
        fetch.return_value = ('https://example.com/1', None, None)

        await crawl.crawl()

        fetch.assert_called_once_with('https://example.com/1')


async def test_fetch():
    with aioresponses() as m:
        m.get(
            'https://example.com/1',
            headers={'Content-Type': 'application/rss+xml'},
            body='''<?xml version="1.0"?>
            <rss version="2.0">
                <channel>
                    <title>Example!</title>
                    <link>http://www.example.com</link>
                    <item>
                        <description>Great stuff!</description>
                        <guid>abcdefg</guid>
                    </item>
                </channel>
            </rss>
            '''
        )

        feed_url, feed, entries = await crawl.fetch('https://example.com/1')

        assert feed_url == 'https://example.com/1'
        assert feed == {
            'title': 'Example!',
            'link': 'http://www.example.com'
        }
        assert entries == [
            {
                'description': 'Great stuff!',
                'guid': 'abcdefg'
            }
        ]


async def test_fetch_error_status():
    with aioresponses() as m:
        m.get(
            'https://example.com/1',
            status=500,
            headers={'Content-Type': 'application/rss+xml'},
            body='any old thing'
        )

        feed_url, feed, entries = await crawl.fetch('https://example.com/1')

        assert feed_url == 'https://example.com/1'
        assert feed is None
        assert entries is None
