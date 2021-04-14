import aiosqlite

DATABASE_PATH = '/feeds/skim.db'


async def all():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM entries') as cursor:
            async for row in cursor:
                yield row


async def add(feed, id=None, timestamp=None, title=None, link=None, body=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = """
        INSERT OR IGNORE INTO entries (feed, id, timestamp, title, link, body)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        parameters = [feed, id, timestamp, title, link, body]
        await db.execute(query, parameters)
        await db.commit()
