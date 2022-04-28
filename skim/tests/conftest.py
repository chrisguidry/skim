from unittest import mock

import pytest

from skim import database


@pytest.fixture
async def unmigrated_db():
    async with database.connection() as connection:
        with mock.patch.object(database, 'connection') as connection_manager:
            connection_manager.return_value.__aenter__.return_value = connection
            transaction = connection.transaction()
            await transaction.start()
            try:
                yield connection
            finally:
                await transaction.rollback()


@pytest.fixture
async def skim_db(unmigrated_db):
    await database.migrate()
    return unmigrated_db
