import asyncio
import pathlib
import aiohttp
import jinja2
import aiohttp_jinja2
import aiozipkin as az

from aiohttp import web


service_b_api = 'http://127.0.0.1:9002/api/v1/data'
service_e_api = 'http://127.0.0.1:9005/api/v1/data'
host = '127.0.0.1'
port = 9001
zipkin_address = 'http://127.0.0.1:9411'


async def handler(request):
    await asyncio.sleep(0.01)
    session = request.app['session']
    span = az.request_span(request)
    ctx = {'span_context': span.context}

    resp = await session.get(service_b_api, trace_request_ctx=ctx)
    data_b = await resp.json()

    resp = await session.get(service_e_api, trace_request_ctx=ctx)
    data_e = await resp.json()

    tree = {
        'name': 'service_a',
        'host': host,
        'port': port,
        'children': [data_b, data_e],
    }
    ctx = {
        'zipkin':  zipkin_address,
        'service': tree
    }
    return aiohttp_jinja2.render_template('index.html', request, ctx)


async def make_app():

    app = web.Application()
    app.router.add_get('/api/v1/data', handler)
    app.router.add_get('/', handler)

    endpoint = az.create_endpoint('service_a', ipv4=host, port=port)
    tracer = az.create(zipkin_address, endpoint, sample_rate=1.0)

    trace_config = az.make_trace_config(tracer)

    session = aiohttp.ClientSession(trace_configs=[trace_config])
    app['session'] = session

    async def close_session(app):
        await app['session'].close()
    app.on_cleanup.append(close_session)

    az.setup(app, tracer)

    TEMPLATES_ROOT = pathlib.Path(__file__).parent / 'templates'
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(str(TEMPLATES_ROOT)))

    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(make_app())
    web.run_app(app, host=host, port=port)
