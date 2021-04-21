from skim import database, dates


def all():
    return _query_results("""
        SELECT  *
        FROM    entries
        ORDER BY timestamp DESC
    """)


def older_than(timestamp, limit=100):
    return _query_results("""
        SELECT  *
        FROM    entries
        WHERE   timestamp < ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, [timestamp.isoformat(), limit])


async def _query_results(query, parameters=None):
    async with database.connection() as db:
        async with db.execute(query, parameters or []) as cursor:
            async for row in cursor:
                entry = dict(row)
                entry['timestamp'] = dates.from_iso(entry['timestamp'])
                yield entry


async def add(feed, id, timestamp=None, title=None, link=None, body=None):
    async with database.connection() as db:
        query = """
        INSERT OR REPLACE INTO entries (feed, id, timestamp, title, link, body)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        parameters = [feed, id, timestamp.isoformat(), title, link, body]
        await db.execute(query, parameters)
        await db.commit()
