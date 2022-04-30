from skim import database


def all_entries():
    return _query_results(
        """
        SELECT  entries.feed,
                entries.id,
                entries.timestamp,
                entries.title,
                entries.link,
                entries.body,
                entry_creators.creator,
                entry_categories.category
        FROM    entries
                LEFT JOIN  entry_creators
                        ON entry_creators.feed = entries.feed AND
                           entry_creators.id = entries.id
                LEFT JOIN  entry_categories
                        ON entry_categories.feed = entries.feed AND
                           entry_categories.id = entries.id
        ORDER BY timestamp DESC
    """
    )


def older_than(timestamp, filters, limit=100):
    parameters = [timestamp]
    where = f'timestamp < ${len(parameters)} '

    if feed := filters.get('feed'):
        parameters.append(feed)
        where += f'AND entries.feed = ${len(parameters)} '

    if creator := filters.get('creator'):
        parameters.append(creator)
        where += f'AND entry_creators.creator = ${len(parameters)} '

    if category := filters.get('category'):
        parameters.append(category)
        where += f'AND entry_categories.category = ${len(parameters)} '

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
        GROUP BY entries.feed,
                 entries.id,
                 entries.timestamp,
                 entries.title,
                 entries.link,
                 entries.body
        ORDER BY entries.timestamp DESC
        LIMIT ${len(parameters)}
    )
    SELECT  filtered.feed,
            filtered.id,
            filtered.timestamp,
            filtered.title,
            filtered.link,
            filtered.body,
            entry_creators.creator,
            entry_categories.category
    FROM    filtered
            LEFT JOIN  entry_creators
                    ON entry_creators.feed = filtered.feed AND
                       entry_creators.id = filtered.id
            LEFT JOIN  entry_categories
                    ON entry_categories.feed = filtered.feed AND
                       entry_categories.id = filtered.id
    ORDER BY filtered.timestamp DESC
    """
    return _query_results(query, parameters)


async def _query_results(query, parameters=None):
    parameters = parameters or []
    async with database.connection() as db:
        entry = {'feed': None, 'id': None}
        for row in await db.fetch(query, *parameters):
            if (row['feed'], row['id']) == (entry['feed'], entry['id']):
                entry['creators'].add(row['creator'])
                entry['categories'].add(row['category'])
                continue

            if entry['feed'] and entry['id']:
                entry['creators'].discard(None)
                entry['categories'].discard(None)
                yield entry

            entry = dict(row)
            entry['timestamp'] = entry['timestamp']

            entry['creators'] = {entry.pop('creator', None)}
            entry['categories'] = {entry.pop('category', None)}

        if entry['feed'] and entry['id']:
            entry['creators'].discard(None)
            entry['categories'].discard(None)
            yield entry


async def add_all(feed, entries):
    async with database.connection() as db:
        new_entries = 0
        entries = list(entries)
        seen, _ = await partition_by_seen(feed, entries, db)
        for entry in entries:
            if entry['id'] in seen:
                continue
            new = await add(feed, **entry, db=db)
            new_entries += 1 if new else 0
        return new_entries


async def partition_by_seen(feed, entries, db):
    ids = [entry['id'] for entry in entries]

    id_parameters = ', '.join(f'${i+2}' for i in range(len(ids)))
    query = (
        f'SELECT entries.id FROM entries WHERE feed = $1 AND id in ({id_parameters});'
    )

    seen = set(row['id'] for row in await db.fetch(query, feed, *ids))
    unseen = set(ids) - seen

    return seen, unseen


async def add(  # pylint: disable=too-many-arguments
    feed,
    id,  # pylint: disable=redefined-builtin
    timestamp=None,
    title=None,
    link=None,
    body=None,
    creators=None,
    categories=None,
    db=None,
):
    async with database.connection() as db:
        query = """
        INSERT INTO entries (feed, id, timestamp, title, link, body)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT DO NOTHING
        """
        status = await db.execute(query, feed, id, timestamp, title, link, body)
        # status will be a string like "INSERT 0 1"
        was_new = sum(map(int, status.split()[1:])) > 0

        for creator in creators or []:
            query = """
            INSERT INTO entry_creators (feed, id, creator)
            VALUES ($1, $2, $3)
            ON CONFLICT DO NOTHING
            """
            await db.execute(query, feed, id, creator)

        for category in categories or []:
            query = """
            INSERT INTO entry_categories (feed, id, category)
            VALUES ($1, $2, $3)
            ON CONFLICT DO NOTHING
            """
            await db.execute(query, feed, id, category)

        return was_new
