from unittest import mock

import pytest

from skim import crawl, subscriptions


@pytest.fixture
async def two_subscriptions(skim_db):
    await subscriptions.add('https://example.com/1')
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
