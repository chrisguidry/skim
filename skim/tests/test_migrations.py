import tempfile

import pytest

from skim import database, dates


@pytest.fixture(autouse=True)
def example_migrations():
    original = database.MIGRATIONS_BASE
    database.MIGRATIONS_BASE = '/skim/skim/tests/migrations/'
    try:
        yield
    finally:
        database.MIGRATIONS_BASE = original


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


async def test_no_migrations_at_all(empty_migrations, unmigrated_db):
    await database.migrate()

    async with database.connection() as db:
        current_version = await database.current_version(db)
        assert current_version == 0


async def test_applying_migrations_increments_user_version(unmigrated_db):
    await database.migrate()

    async with database.connection() as db:
        current_version = await database.current_version(db)
        assert current_version == 3


async def test_applying_migrations_executes_scripts(unmigrated_db):
    await database.migrate()

    async with database.connection() as db:
        # will raise if migration 0001.foo.sql hasn't run
        await db.execute('SELECT * FROM testing;')


async def test_skips_applied_migrations(unmigrated_db):
    async with database.connection() as db:
        current_version = await database.current_version(db)
        assert current_version == 0
        await db.execute(
            'INSERT INTO migrations (version, applied) VALUES ($1, $2)',
            3,
            dates.utcnow(),
        )

    await database.migrate()

    async with database.connection() as db:
        table_query = '''
        SELECT  COUNT(*)
        FROM    information_schema.tables
        WHERE   table_type = 'table' AND
                table_name = 'testing';
        '''
        count = await db.fetchval(table_query)
        # since we "faked" migration 3,
        # we should not have a "testing" table
        assert count == 0
