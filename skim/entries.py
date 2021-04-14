from skim import database


async def all():
    async with database.connection() as db:
        async with db.execute('SELECT * FROM entries') as cursor:
            async for row in cursor:
                yield row


async def add(feed, id=None, timestamp=None, title=None, link=None, body=None):
    async with database.connection() as db:
        query = """
        INSERT OR IGNORE INTO entries (feed, id, timestamp, title, link, body)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        parameters = [feed, id, timestamp, title, link, body]
        await db.execute(query, parameters)
        await db.commit()
