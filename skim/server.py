from functools import partial

import aiohttp_jinja2
import jinja2
from aiohttp import web
from opentelemetry import trace
from opentelemetry.semconv.trace import SpanAttributes

from . import frontend

tracer = trace.get_tracer(__name__)

server_routes = web.RouteTableDef()


def create_application():
    app = web.Application(middlewares=[trace_requests])

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
        crawl_sparkline=frontend.crawl_sparkline,
    )

    app.add_routes(frontend.routes)
    app.add_routes(server_routes)
    return app


@server_routes.get('/health')
async def health(request: web.Request):
    return web.Response(status=204)


@web.middleware
async def trace_requests(request: web.Request, handler):
    route = request.match_info.route

    if route.resource and route.resource.canonical == '/health':
        return await handler(request)

    canonical_name = route.resource.canonical if route.resource else 'TODO'
    with tracer.start_as_current_span(
        f'{route.method} {canonical_name}',
        kind=trace.SpanKind.SERVER,
    ) as span:
        span.set_attributes(
            {
                SpanAttributes.HTTP_METHOD: request.method,
                SpanAttributes.HTTP_SCHEME: request.scheme,
                SpanAttributes.HTTP_URL: str(request.url),
                SpanAttributes.HTTP_HOST: request.headers['Host'],
                SpanAttributes.HTTP_USER_AGENT: request.headers.get('User-Agent', ''),
                SpanAttributes.HTTP_ROUTE: canonical_name,
            }
        )
        response = await handler(request)
        span.set_attributes({'http.status_code': response.status})
        return response


def run():  # pragma: no cover
    app = create_application()
    web.run_app(app, host='0.0.0.0', port=5000)
