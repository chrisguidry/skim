from collections import defaultdict
from datetime import date

from skim import database


async def top_categories_by_month():
    async with database.connection() as db:
        query = """
        WITH
        by_month AS (
            SELECT  DATE_TRUNC('month', timestamp) as month,
                    category,
                    COUNT(DISTINCT entries.id) as entries
            FROM    entries
                    INNER JOIN entry_categories
                            ON entry_categories.feed = entries.feed AND
                            entry_categories.id = entries.id
            WHERE   category NOT IN ('Uncategorized', 'post')
            GROUP BY month, category
            ORDER BY month DESC, entries DESC
        ),
        ranked AS (
            SELECT  month,
                    category,
                    entries,
                    RANK() OVER (
                        PARTITION BY month
                        ORDER BY entries DESC
                    )
            FROM    by_month
        )
        SELECT  month as start,
                month + (INTERVAL '1 month') as end,
                category,
                entries
        FROM    ranked
        WHERE   rank <= 20 AND
                month >= (DATE_TRUNC('month', CURRENT_TIMESTAMP) - INTERVAL '1 year')
        ORDER BY month DESC, entries DESC
        ;
        """
        results: dict[date, list[str]] = defaultdict(list)

        for row in await db.fetch(query):
            results[row["start"], row['end']].append(row["category"])

        return results
