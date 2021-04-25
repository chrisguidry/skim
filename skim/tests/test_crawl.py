from unittest import mock

import pytest
from aioresponses import aioresponses
from yarl import URL

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
            (
                'https://example.com/1',
                mock.Mock(status=200, content_type='application/rss+xml'),
                {'title': 'One'},
                [
                    {
                        'id': 'entry-one',
                        'title': 'Entry One'
                    }
                ]
            ),
            (
                'https://example.com/2',
                mock.Mock(status=200, content_type='application/rss+xml'),
                {'title': 'Two'},
                [
                    {
                        'id': 'entry-two',
                        'title': 'Entry Two'
                    }
                ])
        ]

        await crawl.crawl()

        fetch.assert_has_calls([
            mock.call('https://example.com/1', caching=None),
            mock.call('https://example.com/2', caching=None)
        ])

        by_feed = {s['feed']: s async for s in subscriptions.all()}

        assert by_feed == {
            'https://example.com/1': {
                'feed': 'https://example.com/1',
                'title': 'One',
                'site': None,
                'icon': None,
                'caching': None
            },
            'https://example.com/2': {
                'feed': 'https://example.com/2',
                'title': 'Two',
                'site': None,
                'icon': None,
                'caching': None
            }
        }


async def test_crawl_fetch_errors(one_subscription):
    with mock.patch('skim.crawl.fetch') as fetch:
        fetch.return_value = (
            'https://example.com/1',
            mock.Mock(status=500, content_type='application/rss+xml'),
            None,
            None
        )

        await crawl.crawl()

        fetch.assert_called_once_with('https://example.com/1', caching=None)


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

        feed_url, response, feed, entries = await crawl.fetch(
            'https://example.com/1'
        )

        assert feed_url == 'https://example.com/1'
        assert response.status == 200
        assert feed == {
            'title': 'Example!',
            'link': 'http://www.example.com',
            'skim:caching': {},
            'skim:namespaces': {
                'http://www.w3.org/2005/Atom': 'atom',
                'http://purl.org/dc/elements/1.1/': 'dc'
            }
        }
        assert entries == [
            {
                'description': 'Great stuff!',
                'guid': 'abcdefg'
            }
        ]


async def test_fetch_sends_user_agent():
    with aioresponses() as m:
        m.get('https://example.com/1', status=304)

        await crawl.fetch('https://example.com/1')

        request = m.requests[('GET', URL('https://example.com/1'))][0]
        sent_headers = request.kwargs['headers']

        assert sent_headers['User-Agent'] == 'skim/0'


async def test_fetch_sends_caching_headers():
    with aioresponses() as m:
        m.get('https://example.com/1', status=304)

        await crawl.fetch(
            'https://example.com/1',
            caching={'Etag': 'the-etag', 'Last-Modified': 'yesterday?'}
        )

        request = m.requests[('GET', URL('https://example.com/1'))][0]
        sent_headers = request.kwargs['headers']

        assert sent_headers['If-None-Match'] == 'the-etag'
        assert sent_headers['If-Modified-Since'] == 'yesterday?'


async def test_fetch_handles_304_responses():
    with aioresponses() as m:
        m.get(
            'https://example.com/1',
            status=304,
            headers={'Content-Type': 'application/rss+xml'},
        )

        feed_url, response, feed, entries = await crawl.fetch(
            'https://example.com/1',
            caching={'Etag': 'the-etag', 'Last-Modified': 'yesterday?'}
        )

        assert feed_url == 'https://example.com/1'
        assert response.status == 304
        assert feed is None
        assert entries is None


async def test_fetch_error_status():
    with aioresponses() as m:
        m.get(
            'https://example.com/1',
            status=500,
            headers={'Content-Type': 'application/rss+xml'},
            body='any old thing'
        )

        feed_url, response, feed, entries = await crawl.fetch(
            'https://example.com/1'
        )

        assert feed_url == 'https://example.com/1'
        assert response.status == 500
        assert feed is None
        assert entries is None
