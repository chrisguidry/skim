import asyncio
from datetime import datetime

from aiohttp import ClientSession
from dateutil.parser import parse as parse_date

from skim import entries, parse, subscriptions


async def crawl():
    fetches = [
        fetch(subscription['feed'])
        async for subscription
        in subscriptions.all()
    ]
    for future_feed in asyncio.as_completed(fetches):
        feed_url, feed, feed_entries = await future_feed
        if not feed:
            continue

        feed = normalize_feed(feed)
        await subscriptions.update(feed_url, **feed)

        entry_saves = [
            entries.add(feed_url, **normalize_entry(entry))
            for entry in feed_entries
        ]
        await asyncio.gather(*entry_saves)


def normalize_feed(feed):
    return {
        'title': feed.get('title'),
        'site': (
            feed.get('link') or
            feed.get('link:alternate')
        ),
        'icon': feed.get('logo')
    }

def normalize_entry(entry):
    return {
        'id': (
            entry.get('id') or
            entry.get('guid') or
            entry.get('uuid') or
            entry.get('link') or
            entry.get('link:alternate')
        ),
        'title': entry.get('title'),
        'link': (
            entry.get('link') or
            entry.get('link:alternate')
        ),
        'timestamp': parse_date(
            entry.get('updated') or
            entry.get('pubDate') or
            entry.get('published') or
            datetime.utcnow().isoformat()
        ),
        'body': (
            entry.get('summary') or
            entry.get('description') or
            entry.get('content')
        )
    }


async def fetch(feed_url):
    headers = {
        'User-Agent': 'skim/0'
    }
    async with ClientSession(headers=headers) as session:
        async with session.get(feed_url) as response:
            if response.status != 200:
                print(
                    'TODO: Error status codes',
                    response.status,
                    response.headers
                )
                return feed_url, None, None

            feed, entries = await parse.parse(response)

            print(f'--- {feed_url} ({response.content_type}) ---')
            import pprint
            pprint.pprint(feed)
            print(f'--- {len(entries)} entries ---')
            # for entry in entries:
            #     pprint.pprint(entry)
            print()

            return feed_url, feed, entries
