import aiohttp_jinja2
import jinja2
from aiohttp import web

from . import frontend

app = web.Application()

aiohttp_jinja2.setup(
    app,
    loader=jinja2.FileSystemLoader('/skim/skim/templates'),
    enable_async=True
)

env = aiohttp_jinja2.get_env(app)
env.filters.update(
    friendly_date=frontend.friendly_date,
    time_ago=frontend.time_ago
)

app.add_routes(frontend.routes)


def run():  # pragma: no cover
    web.run_app(app, host='0.0.0.0', port=5000)
