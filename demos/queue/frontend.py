import asyncio
import aiohttp
import aiozipkin as az

from aiohttp import web


page = """
<html lang="en">
<head>
    <title>aiohttp producer consumer demo</title>
</head>
<body>
    <h1>Your click event send to consumer</h1>
</body>
</html>
"""


backend_service = 'http://127.0.0.1:9011/consume'


async def index(request):
    span = az.request_span(request)
    tracer = az.get_tracer(request.app)
    session = request.app['session']

    with tracer.new_child(span.context) as span_producer:
        span_producer.kind(az.PRODUCER)
        span_producer.name('produce event click')
        span_producer.remote_endpoint('broker', ipv4='127.0.0.1', port=9011)

        headers = span_producer.context.make_headers()
        message = {
            'payload': 'click',
            'headers': headers}
        resp = await session.post(backend_service, json=message)
        resp = await resp.text()
        assert resp == 'ok'

    await asyncio.sleep(0.01)
    return web.Response(text=page, content_type='text/html')


async def make_app(host, port):
    app = web.Application()
    app.router.add_get('/', index)

    session = aiohttp.ClientSession()
    app['session'] = session

    zipkin_address = 'http://127.0.0.1:9411'
    endpoint = az.create_endpoint('frontend', ipv4=host, port=port)
    tracer = await az.create(zipkin_address, endpoint, sample_rate=1.0)
    az.setup(app, tracer)
    return app


if __name__ == '__main__':
    host = '127.0.0.1'
    port = 9010
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(make_app(host, port))
    web.run_app(app, host=host, port=port)
