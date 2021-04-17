import json

from skim import database


async def all():
    async with database.connection() as db:
        async with db.execute('SELECT * FROM subscriptions') as cursor:
            async for row in cursor:
                yield subscription_from_row(row)


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
            row = await cursor.fetchone()
            return subscription_from_row(row) if row else None


async def update(feed, title=None, site=None, icon=None, caching=None):
    async with database.connection() as db:
        query = """
        UPDATE subscriptions
        SET    title = ?,
               site = ?,
               icon = ?,
               caching = ?
        WHERE  feed = ?
        """
        parameters = [
            title,
            site,
            icon,
            json.dumps(caching) if caching else None,

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


def subscription_from_row(row):
    subscription = dict(row)
    if subscription['caching']:
        subscription['caching'] = json.loads(subscription['caching'])
    return subscription
