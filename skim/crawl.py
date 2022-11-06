import asyncio
import logging
import os

from aiohttp import ClientConnectionError, ClientSession, ClientTimeout
from opentelemetry import metrics, trace

from skim import entries, normalize, parse, subscriptions

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)  # type: ignore

new_entries_counter = meter.create_counter(
    'new_entries', '{entries}', 'The number of new entries crawled'
)

MAX_CONCURRENT = int(os.getenv('SKIM_CRAWL_CONCURRENCY') or '8') or 8


async def crawl():
    to_fetch = [
        subscription async for subscription in subscriptions.all_subscriptions()
    ]
    while to_fetch:
        batch, to_fetch = to_fetch[:MAX_CONCURRENT], to_fetch[MAX_CONCURRENT:]
        results = await asyncio.gather(
            *[fetch_and_save(subscription) for subscription in batch],
            return_exceptions=True,
        )
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                subscription = batch[i]
                logger.warning('Exception crawling %s: %r', subscription, result)


async def fetch_and_save(subscription):
    with tracer.start_as_current_span('fetch_and_save') as span:
        feed_url = subscription['feed']
        span.set_attributes({'feed.url': feed_url})
        try:
            feed_url, response, feed, feed_entries = await fetch(
                feed_url, caching=subscription['caching']
            )
            status = response.status
        except (asyncio.TimeoutError, ClientConnectionError):
            feed = None
            status = -1
        except parse.ParseError:
            feed = None
            status = -1
        except Exception:
            print(f'Unhandled exception while crawling {feed_url}')
            raise

        span.set_attributes({'feed.status': status})

        if not feed:
            print(f"Status {status} for {feed_url}")
            await subscriptions.log_crawl(feed_url, status=status)
            return

        feed = normalize.feed(feed)
        await subscriptions.update(feed_url, **feed)

        new_entries = await entries.add_all(
            feed_url, map(normalize.entry, feed_entries)
        )

        span.set_attributes({'feed.new_entries': new_entries})
        new_entries_counter.add(new_entries, {'feed.url': feed_url})

        await subscriptions.log_crawl(
            feed_url,
            status=response.status,
            content_type=response.content_type,
            new_entries=new_entries,
        )


async def fetch(feed_url, caching=None):
    headers = only_set(
        {
            'User-Agent': 'skim/0',
            'If-None-Match': caching and caching.get('Etag'),
            'If-Modified-Since': caching and caching.get('Last-Modified'),
        }
    )
    timeout = ClientTimeout(total=5)
    async with ClientSession(timeout=timeout) as session:
        async with session.get(feed_url, headers=headers) as response:
            print(f'--- {feed_url} ({response.status}) ---')

            if response.status == 304:
                return feed_url, response, None, None

            if response.status != 200:
                print(
                    'TODO: Error status codes',
                    feed_url,
                    response.status,
                    response.headers,
                )
                return feed_url, response, None, None

            print(f'Content: {response.content_type} {response.charset}')

            feed, entries = await parse.parse(
                response.content_type, response.charset, response.content
            )

            feed['skim:caching'] = only_set(
                {
                    'Etag': response.headers.get('Etag'),
                    'Last-Modified': response.headers.get('Last-Modified'),
                }
            )

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
