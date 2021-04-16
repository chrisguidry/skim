from aiohttp import web
from aiohttp_jinja2 import template

from skim import entries

routes = web.RouteTableDef()

STATIC_ROOT = '/skim/skim/static'


routes.static('/static', f'{STATIC_ROOT}', show_index=True)


@routes.get('/')
@template('home.html')
async def home(request):
    return {'entries': entries.all()}
