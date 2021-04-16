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

app.add_routes(frontend.routes)


def run():  # pragma: no cover
    web.run_app(app, host='0.0.0.0', port=5000)
