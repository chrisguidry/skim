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


async def test_subscriptions_management():
    before = await subscriptions.get('https://example.com')
    assert not before

    before = [s['feed'] async for s in subscriptions.all()]
    assert 'https://example.com' not in before

    await subscriptions.add('https://example.com')

    after = await subscriptions.get('https://example.com')
    assert after['feed'] == 'https://example.com'

    after = [s['feed'] async for s in subscriptions.all()]
    assert 'https://example.com' in after

    await subscriptions.remove('https://example.com')

    after = await subscriptions.get('https://example.com')
    assert not after

    after = [s['feed'] async for s in subscriptions.all()]
    assert 'https://example.com' not in after


async def test_subscriptions_updating_data():
    await subscriptions.add('https://example.com')
    await subscriptions.update(
        'https://example.com',
        title='Example!'
    )
    after = await subscriptions.get('https://example.com')
    assert after['title'] == 'Example!'
