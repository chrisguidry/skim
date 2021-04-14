from datetime import datetime
import os

import pytest

from skim import entries, migrations


@pytest.fixture(autouse=True)
async def test_db():
    TEST_PATH = '/tmp/test.db'

    original = entries.DATABASE_PATH

    migrations.DATABASE_PATH = TEST_PATH
    entries.DATABASE_PATH = TEST_PATH

    try:
        os.remove(TEST_PATH)
    except FileNotFoundError:
        pass

    await migrations.migrate()

    try:
        yield TEST_PATH
    finally:
        migrations.DATABASE_PATH = original
        entries.DATABASE_PATH = original


async def test_entries_adding():
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
