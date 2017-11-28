import asyncio
import aiohttp
import aiozipkin as az

from aiohttp import web


service_b_api = 'http://127.0.0.1:9002/api/v1/data'
service_e_api = 'http://127.0.0.1:9005/api/v1/data'


async def index(request):
    body = """
    <html lang="en">
    <head>
        <title>aiohttp microservices</title>
    </head>
    <body>
    <a href="http://127.0.0.1:9001/api/v1/data">Call API</a>
    </body>
    </html>
    """
    return web.Response(text=body, content_type='text/html')


async def handler(request):
    await asyncio.sleep(0.01)
    session = request.app['session']

    resp = await session.get(service_b_api)
    data_b = await resp.text()

    resp = await session.get(service_e_api)
    data_e = await resp.text()

    body = 'service_a ' + data_b + ' ' + data_e
    return web.Response(text=body)


def make_app():
    app = web.Application()
    app.router.add_get('/api/v1/data', handler)
    app.router.add_get('/', index)

    zipkin_address = 'http://127.0.0.1:9411'
    endpoint = az.create_endpoint('service_a')
    tracer = az.create(zipkin_address, endpoint, sample_rate=1.0)

    trace_config = az.make_trace_config(tracer)
    session = aiohttp.ClientSession(trace_configs=[trace_config])
    app['session'] = session

    az.setup(app, tracer)
    return app


if __name__ == '__main__':
    host = '127.0.0.1'
    port = 9001
    app = make_app()
    web.run_app(app, host=host, port=port)
