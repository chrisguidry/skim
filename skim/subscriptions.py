import json

from skim import database, dates


async def all_subscriptions(lookback='14 day'):
    async with database.connection() as db:
        query = f"""
        SELECT  subscriptions.feed,
                subscriptions.title,
                subscriptions.site,
                subscriptions.caching,
                subscriptions.icon,
                ARRAY_AGG(
                    ROW(
                        crawls.crawled,
                        crawls.status,
                        crawls.new_entries
                    )
                ) AS recent_crawls,
                SUM(crawls.new_entries) AS total_new_entries,
                (
                    SELECT MIN(crawled)
                    FROM   crawl_log
                    WHERE  (
                        crawled >=
                        date_trunc('day', current_timestamp - interval '{lookback}')
                    )
                ) AS earliest_crawl,
                (
                    SELECT percentile_disc(0.999) within group (order by new_entries)
                    FROM   crawl_log
                    WHERE  (
                        crawled >=
                        date_trunc('day', current_timestamp - interval '{lookback}')
                    )
                ) AS p95_new_entries
        FROM    subscriptions
                LEFT JOIN (
                    SELECT  feed,
                            crawled,
                            status,
                            new_entries
                    FROM    crawl_log
                    WHERE   (
                        crawled >=
                        date_trunc('day', current_timestamp - interval '{lookback}')
                    )
                    ORDER BY feed, crawled
                ) crawls
                ON crawls.feed = subscriptions.feed
        GROUP BY subscriptions.feed,
                subscriptions.title,
                subscriptions.site,
                subscriptions.caching,
                subscriptions.icon
        ORDER BY subscriptions.title
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
    if 'recent_crawls' in subscription:
        crawls_columns = ['crawled', 'status', 'new_entries']
        subscription['recent_crawls'] = [
            dict(zip(crawls_columns, c)) for c in subscription['recent_crawls']
        ]
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
