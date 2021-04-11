from aiohttp import web

from . import routes


app = web.Application()
app.add_routes(routes)


if __name__ == '__main__':  # pragma: no cover
    web.run_app(app, host='0.0.0.0', port=5000)
