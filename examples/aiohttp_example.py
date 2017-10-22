import asyncio

import aiohttp
import aiozipkin as az

from aiohttp import web


zipkin_address = 'http://127.0.0.1:9411'


async def handle(request):
    tracer = az.get_tracer(request.app)
    span = az.request_span(request)

    with tracer.new_child(span.context) as child_span:
        child_span.name('mysql:select')
        await asyncio.sleep(0.01)

    text = 'Hello'
    return web.Response(text=text)


def make_app(host, port, loop):
    app = web.Application()
    endpoint = az.create_endpoint(
        'aiohttp_server', ipv4=host, port=port)
    tracer = az.create(zipkin_address, endpoint, sample_rate=1.0)
    az.setup(app, tracer)

    app.router.add_get('/', handle)
    app.router.add_get('/api/v1/posts/{entity_id}', handle)
    return app


async def run_server(loop):
    host = '127.0.0.1'
    port = 8080
    app = make_app(host, port, loop)
    handler = app.make_handler()
    await loop.create_server(handler, host, port)
    return handler


async def run_client(loop):
    endpoint = az.create_endpoint('aiohttp_client')
    tracer = az.create(zipkin_address, endpoint, sample_rate=1.0)
    session = aiohttp.ClientSession(loop=loop)

    for i in range(1000):
        with tracer.new_trace() as span:
            span.kind(az.CLIENT)
            headers = span.context.make_headers()
            host = 'http://127.0.0.1:8080/api/v1/posts/{}'.format(i)
            resp = await session.get(host, headers=headers)
            await resp.text()
        await asyncio.sleep(5, loop=loop)


def run():
    loop = asyncio.get_event_loop()
    handler = loop.run_until_complete(run_server(loop))
    try:
        loop.run_until_complete(run_client(loop))
    except KeyboardInterrupt:
        loop.run_until_complete(handler.finish_connections())


if __name__ == '__main__':
    run()
