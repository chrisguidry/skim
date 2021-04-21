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
