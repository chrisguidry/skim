import aiofiles
import aiofiles.os
import pytest
from aiohttp import web

from skim import routes


@pytest.fixture
def client(loop, aiohttp_client):
    app = web.Application()
    app.add_routes(routes)
    return loop.run_until_complete(aiohttp_client(app))


EMPTY_SUBSCRIPTIONS = '<opml></opml>'


@pytest.fixture
async def empty_subscriptions():
    try:
        await aiofiles.os.remove('/feeds/subscriptions.opml')
    except FileNotFoundError:
        pass


EXAMPLE_SUBSCRIPTIONS = """<?xml version='1.0' encoding='UTF-8'?>
<opml>
    <body>
        <outline text='Example A'
                 type='rss'
                 xmlUrl='https://example.com/feedA.xml' />
        <outline text='Example B'
                 type='rss'
                 xmlUrl='https://example.com/feedB.xml' />
    </body>
</opml>
"""


@pytest.fixture
async def example_subscriptions():
    async with aiofiles.open('/feeds/subscriptions.opml', 'w') as opmlfile:
        await opmlfile.write(EXAMPLE_SUBSCRIPTIONS)


async def test_get_subscriptions_empty(client, empty_subscriptions):
    response = await client.get('/subscriptions')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/x-opml; charset=utf-8'
    assert await response.text() == EMPTY_SUBSCRIPTIONS


async def test_put_subscriptions(client, empty_subscriptions):
    response = await client.put('/subscriptions', data=EXAMPLE_SUBSCRIPTIONS)
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/x-opml; charset=utf-8'
    assert await response.text() == EXAMPLE_SUBSCRIPTIONS

    response = await client.get('/subscriptions')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/x-opml; charset=utf-8'
    assert await response.text() == EXAMPLE_SUBSCRIPTIONS


async def test_delete_subscriptions(client, example_subscriptions):
    response = await client.get('/subscriptions')
    assert await response.text() == EXAMPLE_SUBSCRIPTIONS

    response = await client.delete('/subscriptions')
    assert response.status == 204

    response = await client.get('/subscriptions')
    assert await response.text() == EMPTY_SUBSCRIPTIONS


async def test_delete_subscriptions_idempotent(client, empty_subscriptions):
    response = await client.get('/subscriptions')
    assert await response.text() == EMPTY_SUBSCRIPTIONS

    response = await client.delete('/subscriptions')
    assert response.status == 204

    response = await client.get('/subscriptions')
    assert await response.text() == EMPTY_SUBSCRIPTIONS
