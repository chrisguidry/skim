import asyncio

from aiohttp import ClientSession

from skim import parse, subscriptions


async def crawl():
    tasks = [
        fetch(subscription)
        async for subscription
        in subscriptions.all()
    ]
    await asyncio.gather(*tasks)

async def fetch(subscription):
    headers = {
        'User-Agent': 'skim/0'
    }
    async with ClientSession(headers=headers) as session:
        async with session.get(subscription['feed']) as response:
            if response.status != 200:
                print(
                    'TODO: Error status codes',
                    response.status,
                    response.headers
                )
                return

            feed, entries = await parse.parse(response)

            print('\n--- RESULTS ---')
            import pprint
            pprint.pprint(feed)
            print('---')
            for entry in entries:
                pprint.pprint(entry)
