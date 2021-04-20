from datetime import datetime

from skim import database


async def all():
    async with database.connection() as db:
        query = """
        SELECT  *
        FROM    entries
        ORDER BY timestamp DESC
        """
        async with db.execute(query) as cursor:
            async for row in cursor:
                entry = dict(row)
                entry['timestamp'] = from_iso(entry['timestamp'])
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


def from_iso(isostring):
    if '.' in isostring:
        return datetime.strptime(isostring, '%Y-%m-%dT%H:%M:%S.%f%z')
    else:
        return datetime.strptime(isostring, '%Y-%m-%dT%H:%M:%S%z')
