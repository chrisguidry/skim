from datetime import datetime, timezone

import pytest

from skim import entries, server, subscriptions


@pytest.fixture
def client(loop, aiohttp_client):
    return loop.run_until_complete(aiohttp_client(server.app))


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
            timestamp=datetime(2021, 1, 2, 3 + i, tzinfo=timezone.utc)
        )


async def test_get_home(client, a_subscription, some_entries):
    response = await client.get('/')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    # TODO: more tests
