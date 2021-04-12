import os

import aiosqlite
import pytest

from skim import migrations, subscriptions


@pytest.fixture(autouse=True)
async def test_db():
    TEST_PATH = '/tmp/test.db'

    original = subscriptions.DATABASE_PATH

    migrations.DATABASE_PATH = TEST_PATH
    subscriptions.DATABASE_PATH = TEST_PATH

    try:
        os.remove(TEST_PATH)
    except FileNotFoundError:
        pass

    await migrations.migrate()

    try:
        yield TEST_PATH
    finally:
        migrations.DATABASE_PATH = original
        subscriptions.DATABASE_PATH = original


async def test_subscriptions_editing(test_db):
    before = [s['feed'] async for s in subscriptions.all()]
    assert 'https://example.com' not in before

    await subscriptions.add('https://example.com')

    after = [s['feed'] async for s in subscriptions.all()]
    assert 'https://example.com' in after

    await subscriptions.remove('https://example.com')

    after = [s['feed'] async for s in subscriptions.all()]
    assert 'https://example.com' not in after
