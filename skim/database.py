from contextlib import asynccontextmanager

import aiosqlite

DATABASE_PATH = '/feeds/skim.db'


@asynccontextmanager
async def connection():
    print('opening', DATABASE_PATH)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
