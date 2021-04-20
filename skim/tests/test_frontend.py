from datetime import datetime, timezone

import pytest

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
            timestamp=datetime(2021, 1, 2, 3 + i, tzinfo=timezone.utc)
        )


async def test_get_home(client, a_subscription, some_entries):
    response = await client.get('/')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    assert 'Entry 2' in await response.text()
    # TODO: more tests


async def test_get_subscriptions_list(client, a_subscription):
    response = await client.get('/subscriptions')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    assert 'https://example.com/feed' in await response.text()
    # TODO: more tests
