import os
from contextlib import asynccontextmanager

import aiofiles
import asyncpg
from opentelemetry import trace

from skim import dates

MIGRATIONS_BASE = '/skim/skim/migrations/'

tracer = trace.get_tracer(__name__)


@asynccontextmanager
async def connection():
    db = await asyncpg.connect(**connection_parameters())
    try:
        yield db
    finally:
        await db.close()


def connection_parameters():
    return {
        'host': os.environ['DB_HOST'],
        'port': int(os.environ.get('DB_PORT', '5432')),
        'user': os.environ['DB_USER'],
        'password': os.environ['DB_PASSWORD'],
        'database': os.environ['DB_NAME'],
    }


async def migrate():
    with tracer.start_as_current_span('migrate'):
        async with connection() as db, db.transaction():
            starting_version = await current_version(db)

            async for version, migration in migrations():  # pragma: no branch
                if version <= starting_version:
                    print(f'{version} already applied')
                    continue

                print(f'Applying {version}')
                await db.execute(migration)
                await db.execute(
                    'INSERT INTO migrations (version, applied) VALUES ($1, $2)',
                    version,
                    dates.utcnow(),
                )


async def current_version(db) -> int:
    current_version = 0
    try:
        async with db.transaction():
            current_version = await db.fetchval('SELECT MAX(version) FROM migrations;')
    except asyncpg.exceptions.UndefinedTableError:
        await db.execute(
            """
        CREATE TABLE migrations(
            version INT PRIMARY KEY NOT NULL,
            applied timestamptz NOT NULL
        );
        """
        )
    return current_version or 0


async def migrations():
    for migration_filename in sorted(os.listdir(MIGRATIONS_BASE)):
        if not migration_filename.endswith('.sql'):
            continue

        version = int(migration_filename.split('.')[0])
        migration_filename = os.path.join(MIGRATIONS_BASE, migration_filename)

        async with aiofiles.open(migration_filename) as migration_file:
            migration = await migration_file.read()
            yield version, migration
