from skim import database


async def all():
    async with database.connection() as db:
        async with db.execute('SELECT * FROM subscriptions') as cursor:
            async for row in cursor:
                yield row


async def add(feed):
    async with database.connection() as db:
        query = """
        INSERT OR IGNORE INTO subscriptions (feed) VALUES (?)
        """
        parameters = [feed]
        await db.execute(query, parameters)
        await db.commit()


async def get(feed):
    async with database.connection() as db:
        query = 'SELECT * FROM subscriptions WHERE feed = ?'
        parameters = [feed]
        async with db.execute(query, parameters) as cursor:
            return await cursor.fetchone()


async def update(feed, title=None, site=None, icon=None):
    async with database.connection() as db:
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
    async with database.connection() as db:
        query = """
        DELETE FROM subscriptions WHERE feed = ?
        """
        parameters = [feed]
        await db.execute(query, parameters)
        await db.commit()
