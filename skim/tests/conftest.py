import os

import pytest

from skim import database


@pytest.fixture(autouse=True)
def event_loop(loop):
    # uses the aiohttp loop as the pytest-asyncio loop for all tests
    return loop


@pytest.fixture
async def skim_db():
    TEST_PATH = '/tmp/test.db'

    original = database.DATABASE_PATH

    database.DATABASE_PATH = TEST_PATH

    try:
        os.remove(TEST_PATH)
    except FileNotFoundError:
        pass

    await database.migrate()

    try:
        yield TEST_PATH
    finally:
        database.DATABASE_PATH = original
