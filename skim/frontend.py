from datetime import datetime, timezone

import humanize
from aiohttp import web
from aiohttp_jinja2 import template

from skim import entries, subscriptions

routes = web.RouteTableDef()

STATIC_ROOT = '/skim/skim/static'


routes.static('/static', f'{STATIC_ROOT}', show_index=True)


def time_ago(date):
    return humanize.naturaldelta(
        datetime.utcnow().replace(tzinfo=timezone.utc) - date
    )


def friendly_date(date):
    return date.strftime('%A, %B %d, %Y at %I:%M %p (%Z)')


@routes.get('/')
@template('home.html')
async def home(request):
    return {
        'entries': entries.all(),
        'subscriptions': {s['feed']: s async for s in subscriptions.all()}
    }
