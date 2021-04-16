import asyncio

from aiohttp import ClientSession

from skim import entries, normalize, parse, subscriptions


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

        feed = normalize.feed(feed)
        await subscriptions.update(feed_url, **feed)

        entry_saves = [
            entries.add(feed_url, **normalize.entry(entry))
            for entry in feed_entries
        ]
        await asyncio.gather(*entry_saves)


async def fetch(feed_url):
    headers = {
        'User-Agent': 'skim/0'
    }
    async with ClientSession(headers=headers) as session:
        async with session.get(feed_url) as response:
            if response.status != 200:
                print(
                    'TODO: Error status codes',
                    feed_url,
                    response.status,
                    response.headers
                )
                return feed_url, None, None

            feed, entries = await parse.parse(
                response.content_type,
                response.charset,
                response.content
            )

            print(f'--- {feed_url} ({response.content_type}) ---')
            import pprint
            pprint.pprint(feed)
            pprint.pprint(normalize.feed(feed))
            print(f'--- {len(entries)} entries ---')
            for entry in entries:
                pprint.pprint(entry)
                pprint.pprint(normalize.entry(entry))
            print()

            return feed_url, feed, entries
