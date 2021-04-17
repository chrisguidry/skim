import asyncio

from aiohttp import ClientSession

from skim import entries, normalize, parse, subscriptions


async def crawl():
    fetches = [
        fetch(subscription['feed'], caching=subscription['caching'])
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


async def fetch(feed_url, caching=None):
    headers = only_set({
        'User-Agent': 'skim/0',
        'If-None-Match': caching and caching.get('Etag'),
        'If-Modified-Since': caching and caching.get('Last-Modified')
    })
    async with ClientSession() as session:
        async with session.get(feed_url, headers=headers) as response:
            print(f'--- {feed_url} ({response.status}) ---')

            if response.status == 304:
                return feed_url, None, None
            elif response.status != 200:
                print(
                    'TODO: Error status codes',
                    feed_url,
                    response.status,
                    response.headers
                )
                return feed_url, None, None

            print(f'Content: {response.content_type} {response.charset}')

            feed, entries = await parse.parse(
                response.content_type,
                response.charset,
                response.content
            )

            feed['skim:caching'] = only_set({
                'Etag': response.headers.get('Etag'),
                'Last-Modified': response.headers.get('Last-Modified')
            })

            import pprint
            pprint.pprint(feed)
            pprint.pprint(normalize.feed(feed))
            print(f'--- {len(entries)} entries ---')
            # for entry in entries:
            #     pprint.pprint(entry)
            #     pprint.pprint(normalize.entry(entry))

            return feed_url, feed, entries


def only_set(d):
    """Filters a dict to only the keys that have truthy values"""
    return {k: v for k, v in d.items() if v}
