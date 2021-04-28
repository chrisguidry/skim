from skim import database, dates


def all():
    return _query_results("""
        SELECT  *
        FROM    entries
                LEFT JOIN  entry_creators
                        ON entry_creators.feed = entries.feed AND
                           entry_creators.id = entries.id
                LEFT JOIN  entry_categories
                        ON entry_categories.feed = entries.feed AND
                           entry_categories.id = entries.id
        ORDER BY timestamp DESC
    """)


def older_than(timestamp, filters, limit=100):
    parameters = [timestamp.isoformat()]
    where = 'timestamp < ? '

    if feed := filters.get('feed'):
        where += 'AND entries.feed = ? '
        parameters.append(feed)

    if creator := filters.get('creator'):
        where += 'AND entry_creators.creator = ? '
        parameters.append(creator)

    if category := filters.get('category'):
        where += 'AND entry_categories.category = ? '
        parameters.append(category)

    parameters.append(limit)

    query = f"""
    WITH filtered(feed, id, timestamp, title, link, body) AS (
        SELECT  entries.feed,
                entries.id,
                entries.timestamp,
                entries.title,
                entries.link,
                entries.body
        FROM    entries
                LEFT JOIN  entry_creators
                        ON entry_creators.feed = entries.feed AND
                           entry_creators.id = entries.id
                LEFT JOIN  entry_categories
                        ON entry_categories.feed = entries.feed AND
                           entry_categories.id = entries.id
        WHERE   {where}
        ORDER BY entries.timestamp DESC
        LIMIT ?
    )
    SELECT  *
    FROM    filtered
            LEFT JOIN  entry_creators
                    ON entry_creators.feed = filtered.feed AND
                       entry_creators.id = filtered.id
            LEFT JOIN  entry_categories
                    ON entry_categories.feed = filtered.feed AND
                       entry_categories.id = filtered.id
    """
    return _query_results(query, parameters)


async def _query_results(query, parameters=None):
    async with database.connection() as db:
        async with db.execute(query, parameters or []) as cursor:
            entry = {'feed': None, 'id': None}
            async for row in cursor:  # pragma no branch, bug?
                if (row['feed'], row['id']) == (entry['feed'], entry['id']):
                    entry['creators'].add(row['creator'])
                    entry['categories'].add(row['category'])
                    continue

                if (entry['feed'] and entry['id']):
                    entry['creators'].discard(None)
                    entry['categories'].discard(None)
                    yield entry

                entry = dict(row)
                entry['timestamp'] = dates.from_iso(entry['timestamp'])

                entry['creators'] = {entry.pop('creator', None)}
                entry['categories'] = {entry.pop('category', None)}

            if (entry['feed'] and entry['id']):
                entry['creators'].discard(None)
                entry['categories'].discard(None)
                yield entry


async def add_all(feed, entries):
    async with database.connection() as db:
        new_entries = 0
        for entry in entries:
            new = await add(feed, **entry, db=db)
            new_entries += 1 if new else 0
        return new_entries


async def add(
    feed, id,
    timestamp=None, title=None, link=None, body=None,
    creators=None, categories=None,
    db=None
):
    async with database.connection() as db:
        query = """
        INSERT OR IGNORE INTO entries (feed, id, timestamp, title, link, body)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        parameters = [
            feed,
            id,
            timestamp.isoformat(),
            title,
            link,
            body
        ]
        await db.execute(query, parameters)
        was_new = db.total_changes > 0

        for creator in (creators or []):
            query = """
            INSERT OR IGNORE INTO entry_creators (feed, id, creator)
            VALUES (?, ?, ?)
            """
            parameters = [feed, id, creator]
            await db.execute(query, parameters)

        for category in (categories or []):
            query = """
            INSERT OR IGNORE INTO entry_categories (feed, id, category)
            VALUES (?, ?, ?)
            """
            parameters = [feed, id, category]
            await db.execute(query, parameters)

        await db.commit()
        return was_new
