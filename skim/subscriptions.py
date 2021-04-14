import aiosqlite


DATABASE_PATH = '/feeds/skim.db'


async def all():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM subscriptions') as cursor:
            async for row in cursor:
                yield row


async def add(feed):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = """
        INSERT OR IGNORE INTO subscriptions (feed) VALUES (?)
        """
        parameters = [feed]
        await db.execute(query, parameters)
        await db.commit()


async def get(feed):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = 'SELECT * FROM subscriptions WHERE feed = ?'
        parameters = [feed]
        async with db.execute(query, parameters) as cursor:
            return await cursor.fetchone()


async def update(feed, title=None, site=None, icon=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = """
        UPDATE subscriptions
        SET    title = ?,
               site = ?,
               icon = ?
        WHERE  feed = ?
        """
        parameters = [
            title,
            site,
            icon,
            feed
        ]
        await db.execute(query, parameters)
        await db.commit()


async def remove(feed):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = """
        DELETE FROM subscriptions WHERE feed = ?
        """
        parameters = [feed]
        await db.execute(query, parameters)
        await db.commit()
