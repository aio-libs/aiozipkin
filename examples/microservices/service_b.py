import asyncio
import aiohttp
import aiozipkin as az

from aiohttp import web


service_c_api = 'http://127.0.0.1:9003/api/v1/data'
service_d_api = 'http://127.0.0.1:9004/api/v1/data'
host = '127.0.0.1'
port = 9002


async def handler(request):
    await asyncio.sleep(0.01)
    session = request.app['session']

    resp = await session.get(service_c_api)
    data_c = await resp.json()

    resp = await session.get(service_d_api)
    data_d = await resp.json()

    payload = {
        'name': 'service_b',
        'host': host,
        'port': port,
        'children': [data_c, data_d],
    }
    return web.json_response(payload)


async def make_app():
    app = web.Application()
    app.router.add_get('/api/v1/data', handler)

    zipkin_address = 'http://127.0.0.1:9411/api/v2/spans'
    endpoint = az.create_endpoint('service_b', ipv4=host, port=port)
    tracer = await az.create(zipkin_address, endpoint, sample_rate=1.0)
    az.setup(app, tracer)

    trace_config = az.make_trace_config(tracer)

    session = aiohttp.ClientSession(trace_configs=[trace_config])
    app['session'] = session

    async def close_session(app):
        await app['session'].close()

    app.on_cleanup.append(close_session)
    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(make_app())
    web.run_app(app, host=host, port=port)
