import os
import tempfile

import pytest

from skim import database


@pytest.fixture(autouse=True)
def example_migrations():
    original = database.MIGRATIONS_BASE
    database.MIGRATIONS_BASE = '/skim/skim/tests/migrations/'
    try:
        yield
    finally:
        database.MIGRATIONS_BASE = original


@pytest.fixture(autouse=True)
def example_database():
    original = database.DATABASE_PATH
    database.DATABASE_PATH = '/tmp/example.db'
    try:
        os.remove(database.DATABASE_PATH)
    except FileNotFoundError:
        pass

    try:
        yield database.DATABASE_PATH
    finally:
        database.DATABASE_PATH = original


async def test_listing_migrations():
    found = [m async for m in database.migrations()]

    assert len(found) == 2

    version, migration = found[0]
    assert version == 1
    assert 'CREATE TABLE testing' in migration

    version, migration = found[1]
    assert version == 3
    assert 'ALTER TABLE testing' in migration


@pytest.fixture
def empty_migrations(example_migrations):
    original = database.MIGRATIONS_BASE
    with tempfile.TemporaryDirectory() as tempdir:
        database.MIGRATIONS_BASE = tempdir
        try:
            yield
        finally:
            database.MIGRATIONS_BASE = original


async def test_no_migrations_at_all(empty_migrations, example_database):
    await database.migrate()

    async with database.connection() as db:
        async with db.execute('PRAGMA user_version;') as cursor:
            current_version = await cursor.fetchone()
            current_version = current_version[0]

        assert current_version == 0


async def test_applying_migrations_increments_user_version(example_database):
    await database.migrate()

    async with database.connection() as db:
        async with db.execute('PRAGMA user_version;') as cursor:
            current_version = await cursor.fetchone()
            current_version = current_version[0]

        assert current_version == 3


async def test_applying_migrations_executes_scripts(example_database):
    await database.migrate()

    async with database.connection() as db:
        # will raise if migration 0001.foo.sql hasn't run
        await db.execute('SELECT * FROM testing;')


async def test_skips_applied_migrations(example_database):
    async with database.connection() as db:
        await db.execute('PRAGMA user_version = 3;')

    await database.migrate()

    async with database.connection() as db:
        table_query = '''
        SELECT  COUNT(*)
        FROM    sqlite_master
        WHERE   type = 'table' AND
                name = 'testing';
        '''
        async with db.execute(table_query) as cursor:
            # since we "faked" migration 3,
            # we should not have a "testing" table
            count = await cursor.fetchone()
            assert count[0] == 0
