from functools import partial

import aiohttp_jinja2
import jinja2
from aiohttp import web

from . import frontend


def create_application():
    app = web.Application()

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader('/skim/skim/templates'),
        enable_async=True,
    )

    env = aiohttp_jinja2.get_env(app)
    env.filters.update(
        friendly_date=frontend.friendly_date,
        query_string=frontend.query_string,
        time_ago=frontend.time_ago,
        static_file=partial(frontend.static_file, app),
    )

    app.add_routes(frontend.routes)
    return app


def run():  # pragma: no cover
    app = create_application()
    web.run_app(app, host='0.0.0.0', port=5000)
