import aiofiles
import aiosqlite
import os


MIGRATIONS_BASE = os.path.dirname(__file__)
DATABASE = '/feeds/skim.db'


async def migrate():
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('PRAGMA user_version;') as cursor:
            current_version = await cursor.fetchone()
            current_version = current_version[0]

        async for version, migration in migrations():
            if version <= current_version:
                print(f'{version} already applied')
                continue

            print(f'Applying {version}')
            await db.executescript('\n'.join([
                'BEGIN;',
                f'PRAGMA user_version = {version};',
                migration,
                'COMMIT;'
            ]))


async def migrations():
    for migration_filename in sorted(os.listdir(MIGRATIONS_BASE)):
        if not migration_filename.endswith('.sql'):
            continue

        version = int(migration_filename.split('.')[0])
        migration_filename = os.path.join(MIGRATIONS_BASE, migration_filename)

        async with aiofiles.open(migration_filename) as migration_file:
            migration = await migration_file.read()
            yield version, migration
