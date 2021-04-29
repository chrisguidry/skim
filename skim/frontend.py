from datetime import datetime, timezone
from urllib.parse import urlencode

import humanize
from aiohttp import web
from aiohttp_jinja2 import template

from skim import dates, entries, subscriptions

routes = web.RouteTableDef()

END_OF_TIME = datetime.max.replace(tzinfo=timezone.utc)

STATIC_ROOT = '/skim/skim/static'


routes.static('/static', f'{STATIC_ROOT}', show_index=True)


def time_ago(date):
    return humanize.naturaldelta(
        dates.utcnow() - date
    )


def friendly_date(date):
    return date.strftime('%A, %B %d, %Y at %I:%M %p (%Z)')


def query_string(query):
    return urlencode({k: v for k, v in query.items() if v})


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
        'category': request.query.get('category')
    }

    return {
        'filters': filters,
        'entries': entries.older_than(older_than, filters, limit=20),
        'subscriptions': {s['feed']: s async for s in subscriptions.all()}
    }


@routes.get('/subscriptions')
@template('subscriptions.html')
async def subscriptions_list(request):
    return {
        'subscriptions': subscriptions.all()
    }
