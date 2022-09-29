from datetime import datetime, timezone
from unittest import mock

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
            timestamp=datetime(2021, 1, 2, 3 + i, tzinfo=timezone.utc),
            categories=['Cool'],
        )


async def test_get_home(client, a_subscription, some_entries):
    response = await client.get('/')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    soup = BeautifulSoup(await response.text(), 'html.parser')
    entry_links = [a['href'] for a in soup.select('article h1 a[href]')]
    assert entry_links == [
        'https://example.com/2',
        'https://example.com/1',
        'https://example.com/0',
    ]


async def test_get_home_second_page(client, a_subscription, some_entries):
    response = await client.get('/?older-than=2021-01-02T05:00:00Z')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    soup = BeautifulSoup(await response.text(), 'html.parser')
    entry_links = [a['href'] for a in soup.select('article h1 a[href]')]
    assert entry_links == ['https://example.com/1', 'https://example.com/0']


async def test_redirect_on_bad_date(client, a_subscription, some_entries):
    response = await client.get('/?older-than=junk', allow_redirects=False)
    assert response.status == 302
    assert response.headers['Location'] == '/'


async def test_get_subscriptions_list(client, a_subscription):
    response = await client.get('/subscriptions')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    soup = BeautifulSoup(await response.text(), 'html.parser')
    feed_links = [a['href'] for a in soup.select('table td a[href]')]
    assert feed_links == [
        '/?feed=https://example.com/feed',
        'https://example.com/feed',
    ]


async def test_get_subscriptions_opml(client, a_subscription):
    response = await client.get('/subscriptions.opml')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/x-opml; charset=utf-8'

    soup = BeautifulSoup(await response.text(), 'xml')
    print(soup.select('opml body outline'))
    feed_links = [o['xmlUrl'] for o in soup.select('opml body outline')]
    assert feed_links == [
        'https://example.com/feed',
    ]


async def test_add_subscription(skim_db, client):
    response = await client.post(
        '/subscriptions',
        data={'feed': 'https://example.com/feed', 'action': 'add'},
    )
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    soup = BeautifulSoup(await response.text(), 'html.parser')
    feed_links = [a['href'] for a in soup.select('table td a[href]')]
    assert feed_links == [
        '/?feed=https://example.com/feed',
        'https://example.com/feed',
    ]


async def test_add_subscription_empty(skim_db, client):
    response = await client.post('/subscriptions', data={'feed': '', 'action': 'add'})
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    soup = BeautifulSoup(await response.text(), 'html.parser')
    feed_links = [a['href'] for a in soup.select('table td a[href]')]
    assert feed_links == []


async def test_delete_subscription(client, a_subscription):
    response = await client.post(
        '/subscriptions',
        data={'feed': 'https://example.com/feed', 'action': 'delete'},
    )
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    soup = BeautifulSoup(await response.text(), 'html.parser')
    feed_links = [a['href'] for a in soup.select('table td a[href]')]
    assert feed_links == []


@pytest.fixture
def mock_top_categories():
    with mock.patch('skim.frontend.categories.top_categories_by_month') as top:
        top.return_value = {
            (datetime(2022, 9, 1), datetime(2022, 10, 1)): ['a', 'b', 'c'],
            (datetime(2022, 8, 1), datetime(2022, 9, 1)): ['b', 'c', 'd'],
            (datetime(2022, 7, 1), datetime(2022, 8, 1)): ['d', 'c', 'b'],
        }
        yield top


async def test_list_hot_topics(client, mock_top_categories):
    response = await client.get('/hot')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

    soup = BeautifulSoup(await response.text(), 'html.parser')
    category_links = [a['href'] for a in soup.select('ol li a[href]')]
    assert category_links == [
        '/?category=a&older-than=2022-10-01T00%3A00%3A00',
        '/?category=b&older-than=2022-10-01T00%3A00%3A00',
        '/?category=c&older-than=2022-10-01T00%3A00%3A00',
        '/?category=b&older-than=2022-09-01T00%3A00%3A00',
        '/?category=c&older-than=2022-09-01T00%3A00%3A00',
        '/?category=d&older-than=2022-09-01T00%3A00%3A00',
        '/?category=d&older-than=2022-08-01T00%3A00%3A00',
        '/?category=c&older-than=2022-08-01T00%3A00%3A00',
        '/?category=b&older-than=2022-08-01T00%3A00%3A00',
    ]
