import json

from skim import database, dates


async def all_subscriptions():
    async with database.connection() as db:
        query = """
        SELECT  *
        FROM    subscriptions
        ORDER BY title
        """
        for row in await db.fetch(query):
            yield subscription_from_row(row)


async def add(feed):
    async with database.connection() as db:
        insert = """
        INSERT INTO subscriptions (feed) VALUES ($1) ON CONFLICT DO NOTHING
        """
        await db.execute(insert, feed)


async def get(feed):
    async with database.connection() as db:
        query = 'SELECT * FROM subscriptions WHERE feed = $1'
        row = await db.fetchrow(query, feed)
        return subscription_from_row(row) if row else None


async def update(feed, title=None, site=None, icon=None, caching=None):
    async with database.connection() as db:
        query = """
        UPDATE subscriptions
        SET    title = $1,
               site = $2,
               icon = $3,
               caching = $4
        WHERE  feed = $5
        """
        parameters = [
            title,
            site,
            icon,
            json.dumps(caching) if caching else None,
            feed,
        ]
        await db.execute(query, *parameters)


async def remove(feed):
    async with database.connection() as db, db.transaction():
        await db.execute('DELETE FROM subscriptions WHERE feed = $1;', feed)
        await db.execute('DELETE FROM entries WHERE feed = $1;', feed)


def subscription_from_row(row):
    subscription = dict(row)
    if subscription['caching']:
        subscription['caching'] = json.loads(subscription['caching'])
    return subscription


async def log_crawl(feed, status=None, content_type=None, new_entries=None):
    async with database.connection() as db:
        query = """
        INSERT INTO crawl_log (
            feed,
            crawled,
            status,
            content_type,
            new_entries
        )
        VALUES ($1, $2, $3, $4, $5)
        """
        parameters = [
            feed,
            dates.utcnow(),
            status,
            content_type,
            new_entries,
        ]
        await db.execute(query, *parameters)
