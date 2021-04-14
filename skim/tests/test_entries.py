from datetime import datetime

from skim import entries


async def test_entries_adding(skim_db):
    before = [e['id'] async for e in entries.all()]
    assert 'test-id' not in before

    await entries.add(
        'https://example.com',
        id='test-id',
        timestamp=datetime.utcnow().isoformat(),
        title='Test Entry',
        link='https://example.com/1',
        body='Hiiiii'
    )

    after = [e['id'] async for e in entries.all()]
    assert 'test-id' in after
