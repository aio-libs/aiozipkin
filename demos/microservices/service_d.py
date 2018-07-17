import asyncio
import aiozipkin as az

from aiohttp import web


host = '127.0.0.1'
port = 9004


async def handler(request):
    await asyncio.sleep(0.01)
    payload = {
        'name': 'service_d',
        'host': host,
        'port': port,
        'children': [],
    }
    return web.json_response(payload)


async def make_app():
    app = web.Application()
    app.router.add_get('/api/v1/data', handler)

    zipkin_address = 'http://127.0.0.1:9411/api/v2/spans'
    endpoint = az.create_endpoint('service_d', ipv4=host, port=port)
    tracer = await az.create(zipkin_address, endpoint, sample_rate=1.0)
    az.setup(app, tracer)
    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(make_app())
    web.run_app(app, host=host, port=port)
