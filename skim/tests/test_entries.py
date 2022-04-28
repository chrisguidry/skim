from datetime import datetime, timedelta, timezone

import pytest

from skim import entries


async def test_entries_nonexisting(skim_db):
    assert [e async for e in entries.all_entries()] == []


async def test_entries_single_creator(skim_db):
    await entries.add(
        'https://example.com/feed',
        id='test-id',
        timestamp=datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        title='Test Entry',
        link='https://example.com/1',
        body='Hiiiii',
        creators=['Jane'],
        categories=None,
    )

    after = [e async for e in entries.all_entries() if e['id'] == 'test-id'][0]
    assert after == {
        'feed': 'https://example.com/feed',
        'id': 'test-id',
        'timestamp': datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        'title': 'Test Entry',
        'link': 'https://example.com/1',
        'body': 'Hiiiii',
        'creators': {'Jane'},
        'categories': set(),
    }


async def test_entries_single_category(skim_db):
    await entries.add(
        'https://example.com/feed',
        id='test-id',
        timestamp=datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        title='Test Entry',
        link='https://example.com/1',
        body='Hiiiii',
        creators=None,
        categories=['Cool'],
    )

    after = [e async for e in entries.all_entries() if e['id'] == 'test-id'][0]
    assert after == {
        'feed': 'https://example.com/feed',
        'id': 'test-id',
        'timestamp': datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        'title': 'Test Entry',
        'link': 'https://example.com/1',
        'body': 'Hiiiii',
        'creators': set(),
        'categories': {'Cool'},
    }


async def test_entries_adding(skim_db):
    before = [e['id'] async for e in entries.all_entries()]
    assert 'test-id' not in before

    await entries.add(
        'https://example.com/feed',
        id='test-id',
        timestamp=datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        title='Test Entry',
        link='https://example.com/1',
        body='Hiiiii',
        creators=['Jane', 'John'],
        categories=['Cool', 'Stuff'],
    )

    after = [e async for e in entries.all_entries() if e['id'] == 'test-id'][0]
    assert after == {
        'feed': 'https://example.com/feed',
        'id': 'test-id',
        'timestamp': datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        'title': 'Test Entry',
        'link': 'https://example.com/1',
        'body': 'Hiiiii',
        'creators': {'Jane', 'John'},
        'categories': {'Cool', 'Stuff'},
    }


@pytest.fixture
async def filterable_entries(skim_db):
    new = datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc)
    old = datetime(2020, 2, 3, 4, 5, 6, tzinfo=timezone.utc)

    await entries.add(
        'https://example.com/feed',
        id='new-one',
        timestamp=new,
        title='Test Entry',
        link='https://example.com/2',
        body='Hiiiii #2',
        creators=['Jane', 'John'],
        categories=['Cool', 'Stuff'],
    )

    await entries.add(
        'https://example.com/feed/B',
        id='old-one',
        timestamp=old,
        title='Test Entry',
        link='https://example.com/1',
        body='Hiiiii #1',
        creators=['Jane'],
        categories=['Neat', 'Stuff'],
    )

    await entries.add(
        'https://example.com/feed/A',
        id='another-one',
        timestamp=old - timedelta(seconds=1),
        title='Test Entry',
        link='https://example.com/1',
        body='Hiiiii #1',
        creators=['John'],
        categories=['Cool', 'Stuff'],
    )


async def test_entries_older_than(filterable_entries):
    older = [e['id'] async for e in entries.older_than(datetime(2021, 2, 3), {})]
    assert older == ['old-one', 'another-one']


async def test_entries_older_than_ancient(filterable_entries):
    older = [e['id'] async for e in entries.older_than(datetime(1, 2, 3), {})]
    assert older == []


async def test_entries_older_than_by_feed(filterable_entries):
    filters = {'feed': 'https://example.com/feed/B'}
    older = [e['id'] async for e in entries.older_than(datetime(2021, 2, 3), filters)]
    assert older == ['old-one']


async def test_entries_older_than_by_category(filterable_entries):
    filters = {'category': 'Cool'}
    older = [e['id'] async for e in entries.older_than(datetime(2021, 2, 3), filters)]
    assert older == ['another-one']


async def test_entries_older_than_by_creator(filterable_entries):
    filters = {'creator': 'Jane'}
    older = [e['id'] async for e in entries.older_than(datetime(2021, 2, 3), filters)]
    assert older == ['old-one']


async def test_entries_older_than_by_multiple(filterable_entries):
    filters = {
        'feed': 'https://example.com/feed/B',
        'category': 'Neat',
        'creator': 'Jane',
    }
    older = [e['id'] async for e in entries.older_than(datetime(2021, 2, 3), filters)]
    assert older == ['old-one']
