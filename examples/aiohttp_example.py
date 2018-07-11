import asyncio

import aiozipkin as az
from aiohttp import web


async def handle(request):
    tracer = az.get_tracer(request.app)
    span = az.request_span(request)

    with tracer.new_child(span.context) as child_span:
        child_span.name('mysql:select')
        # call to external service like https://python.org
        # or database query
        await asyncio.sleep(0.01)

    text = """
    <html lang="en">
    <head>
        <title>aiohttp simple example</title>
    </head>
    <body>
        <h3>This page was traced by aiozipkin</h3>
        <p><a href="http://127.0.0.1:9001/status">Go to not traced page</a></p>
    </body>
    </html>
    """
    return web.Response(text=text, content_type='text/html')


async def not_traced_handle(request):
    text = """
    <html lang="en">
    <head>
        <title>aiohttp simple example</title>
    </head>
    <body>
        <h3>This page was NOT traced by aiozipkin></h3>
        <p><a href="http://127.0.0.1:9001">Go to traced page</a></p>
    </body>
    </html>
    """
    return web.Response(text=text, content_type='text/html')


async def make_app(host, port):
    app = web.Application()
    app.router.add_get('/', handle)
    # here we aquire reference to route, so later we can command
    # aiozipkin not to trace it
    skip_route = app.router.add_get('/status', not_traced_handle)

    endpoint = az.create_endpoint(
        'aiohttp_server', ipv4=host, port=port)

    zipkin_address = 'http://127.0.0.1:9411/api/v2/spans'
    tracer = await az.create(zipkin_address, endpoint, sample_rate=1.0)
    az.setup(app, tracer, skip_routes=[skip_route])
    return app


def run():
    host = '127.0.0.1'
    port = 9001
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(make_app(host, port))
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    run()
