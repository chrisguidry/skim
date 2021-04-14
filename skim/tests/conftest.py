import os

import pytest

from skim import database, migrations


@pytest.fixture(autouse=True)
async def test_db():
    TEST_PATH = '/tmp/test.db'

    original = database.DATABASE_PATH

    database.DATABASE_PATH = TEST_PATH

    try:
        os.remove(TEST_PATH)
    except FileNotFoundError:
        pass

    await migrations.migrate()

    try:
        yield TEST_PATH
    finally:
        database.DATABASE_PATH = original
