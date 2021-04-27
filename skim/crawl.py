import asyncio

from aiohttp import ClientSession

from skim import entries, normalize, parse, subscriptions

MAX_CONCURRENT = 4


async def crawl():
    fetches = [
        fetch_and_save(subscription)
        async for subscription
        in subscriptions.all()
    ]
    while fetches:
        batch, fetches = fetches[:MAX_CONCURRENT], fetches[MAX_CONCURRENT:]
        await asyncio.gather(*batch)


async def fetch_and_save(subscription):
    feed_url, response, feed, feed_entries = await fetch(
        subscription['feed'],
        caching=subscription['caching']
    )
    if not feed:
        await subscriptions.log_crawl(feed_url, status=response.status)
        return

    feed = normalize.feed(feed)
    await subscriptions.update(feed_url, **feed)

    new_entries = 0
    for entry in feed_entries:
        new = await entries.add(feed_url, **normalize.entry(entry))
        new_entries += 1 if new else 0

    await subscriptions.log_crawl(
        feed_url,
        status=response.status,
        content_type=response.content_type,
        new_entries=new_entries
    )


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
                return feed_url, response, None, None
            elif response.status != 200:
                print(
                    'TODO: Error status codes',
                    feed_url,
                    response.status,
                    response.headers
                )
                return feed_url, response, None, None

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

        # simpler
        print(normalize.feed(feed)['title'])
        for entry in entries:
            entry = normalize.entry(entry)
            print(entry['timestamp'], entry['title'], 'by:', entry['creators'])

        # # verbose
        # import pprint
        # pprint.pprint(feed)
        # pprint.pprint(normalize.feed(feed))
        # print(f'--- {len(entries)} entries ---')
        # for entry in entries:
        #     pprint.pprint(entry)
        #     pprint.pprint(normalize.entry(entry))

    return feed_url, response, feed, entries


def only_set(d):
    """Filters a dict to only the keys that have truthy values"""
    return {k: v for k, v in d.items() if v}
