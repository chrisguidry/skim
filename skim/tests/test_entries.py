from datetime import datetime, timezone

from skim import entries


async def test_entries_adding(skim_db):
    before = [e['id'] async for e in entries.all()]
    assert 'test-id' not in before

    await entries.add(
        'https://example.com/feed',
        id='test-id',
        timestamp=datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        title='Test Entry',
        link='https://example.com/1',
        body='Hiiiii'
    )

    after = [e async for e in entries.all() if e['id'] == 'test-id'][0]
    assert after == {
        'feed': 'https://example.com/feed',
        'id': 'test-id',
        'timestamp': datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        'title': 'Test Entry',
        'link': 'https://example.com/1',
        'body': 'Hiiiii'
    }


def test_from_iso():
    assert (
        entries.from_iso('2021-02-03T04:05:06Z') ==
        datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc)
    )
    assert (
        entries.from_iso('2021-02-03T04:05:06.123456Z') ==
        datetime(2021, 2, 3, 4, 5, 6, 123456, tzinfo=timezone.utc)
    )
