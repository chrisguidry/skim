from datetime import datetime, timezone

import pytest
from bs4 import BeautifulSoup

from skim import entries, server, subscriptions


@pytest.fixture
async def client(aiohttp_client):
    app = server.create_application()
    return await aiohttp_client(app)


@pytest.fixture
async def a_subscription(skim_db):
    await subscriptions.add('https://example.com/feed')


@pytest.fixture
async def some_entries(a_subscription, skim_db):
    for i in range(3):
        await entries.add(
            'https://example.com/feed',
            id=f'uniquely-{i}',
            title=f'Entry {i}',
            link=f'https://example.com/{i}',
            timestamp=datetime(2021, 1, 2, 3 + i, tzinfo=timezone.utc)
        )


async def test_get_home(client, a_subscription, some_entries):
    response = await client.get('/')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    soup = BeautifulSoup(await response.text())
    entry_links = [a['href'] for a in soup.select('article h1 a')]
    assert entry_links == [
        'https://example.com/2',
        'https://example.com/1',
        'https://example.com/0'
    ]


async def test_get_subscriptions_list(client, a_subscription):
    response = await client.get('/subscriptions')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    soup = BeautifulSoup(await response.text())
    feed_links = [a['href'] for a in soup.select('table td a')]
    assert feed_links == [
        'https://example.com/feed'
    ]
