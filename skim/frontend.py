from datetime import datetime, timezone
from urllib.parse import urlencode

import humanize
from aiohttp import web
from aiohttp_jinja2 import template
from markupsafe import Markup

from skim import categories, dates, entries, opml, subscriptions

routes = web.RouteTableDef()

END_OF_TIME = datetime.max.replace(tzinfo=timezone.utc)


routes.static(
    '/static',
    '/skim/skim/static',
    name='static',
    append_version=True,
)


def time_ago(date):
    return humanize.naturaldelta(dates.utcnow() - date)


def friendly_date(date):
    return date.strftime('%A, %B %d, %Y at %I:%M %p (%Z)')


def query_string(query):
    return urlencode({k: v for k, v in query.items() if v})


def static_file(app, filename):
    return app.router['static'].url_for(filename=filename)


def crawl_sparkline(subscription):
    recent_crawls = subscription['recent_crawls']

    earliest_crawl = subscription['earliest_crawl']
    if not earliest_crawl:
        return ""

    now = dates.utcnow()
    timerange = now - earliest_crawl

    width = 336
    height = max(8, subscription['p95_new_entries'])

    bottom = height
    second_width = width / timerange.total_seconds()

    lines = []

    for crawl in recent_crawls:
        if not crawl['crawled']:
            continue
        x = second_width * (crawl['crawled'] - earliest_crawl).total_seconds()
        y = crawl['new_entries'] or 0

        match crawl['status']:
            case _ if 200 <= crawl['status'] < 300:
                color = 'green'
                y = y or -1
                opacity = 0.3 if y == -1 else 1.0
            case 304:
                color = 'green'
                y = -1
                opacity = 0.05
            case _:
                color = 'red'
                y = -1
                opacity = 0.8

        lines.append(
            f'<line x1="{x}" y1="{bottom}" x2="{x}" y2="{bottom - y}" '
            f'stroke="{color}" stroke-opacity="{opacity}" />'
        )

    return Markup(
        f"""
        <svg
            class="sparkline"
            viewBox="0 0 {width} {height + 2}"
            preserveAspectRatio="none"
            vector-effect="non-scaling-stroke"
            role="img"
            xmlns="http://www.w3.org/2000/svg">
            {" ".join(lines)}
        </svg>
    """.strip()
    )


@routes.get('/')
@template('home.html')
async def home(request):
    try:
        older_than = dates.from_iso(request.query['older-than'])
    except KeyError:
        older_than = END_OF_TIME
    except ValueError:
        return web.Response(status=302, headers={'Location': '/'})

    filters = {
        'feed': request.query.get('feed'),
        'creator': request.query.get('creator'),
        'category': request.query.get('category'),
    }

    return {
        'filters': filters,
        'entries': entries.older_than(older_than, filters, limit=20),
        'subscriptions': {
            s['feed']: s async for s in subscriptions.all_subscriptions()
        },
    }


@routes.get("/hot")
@template("hot.html")
async def hot(request):
    return {'months': await categories.top_categories_by_month()}


@routes.get('/subscriptions')
@template('subscriptions.html')
async def subscriptions_list(request):
    return {'subscriptions': subscriptions.all_subscriptions()}


@routes.post('/subscriptions')
@template('subscriptions.html')
async def modify_subscriptions(request):
    data = await request.post()
    if data['feed']:
        if data['action'] == 'delete':
            await subscriptions.remove(data['feed'])
        else:  # data['action'] == 'add':
            await subscriptions.add(data['feed'])
    return await subscriptions_list(request)


@routes.get('/subscriptions.opml')
async def subscriptions_opml(request):
    response = web.Response(
        status=200,
        headers={'Content-Type': 'text/x-opml'},
        text=await opml.from_subscriptions(subscriptions.all_subscriptions()),
    )
    return response
