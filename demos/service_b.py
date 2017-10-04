import asyncio
import aiohttp
import aiozipkin

from aiohttp import web


service_c_api = "http://127.0.0.1:9003/api/v1/data"
service_d_api = "http://127.0.0.1:9004/api/v1/data"


async def handler(request):
    span = aiozipkin.request_span(request)
    headers = span.context.make_headers()

    await asyncio.sleep(0.01)
    session = request.app["session"]

    resp = await session.get(service_c_api, headers=headers)
    data_b = await resp.text()

    resp = await session.get(service_d_api, headers=headers)
    data_e = await resp.text()

    body = data_b + " " + data_e
    return web.Response(text=body)


def make_app():
    app = web.Application()
    app.router.add_get('/api/v1/data', handler)

    session = aiohttp.ClientSession()
    app["session"] = session

    zipkin_address = "http://localhost:9411/api/v2/spans"
    endpoint = aiozipkin.create_endpoint("service_b")
    tracer = aiozipkin.create(zipkin_address, endpoint)
    aiozipkin.setup(app, tracer)
    return app


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 9001
    app = make_app()
    web.run_app(app, host=host, port=port)
