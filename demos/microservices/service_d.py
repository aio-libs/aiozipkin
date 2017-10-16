import asyncio
import aiozipkin

from aiohttp import web


async def handler(request):
    await asyncio.sleep(0.01)
    body = "servcie_d"
    return web.Response(text=body)


def make_app():
    app = web.Application()
    app.router.add_get('/api/v1/data', handler)

    zipkin_address = "http://127.0.0.1:9411"
    endpoint = aiozipkin.create_endpoint("service_d")
    tracer = aiozipkin.create(zipkin_address, endpoint)
    aiozipkin.setup(app, tracer)
    return app


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 9004
    app = make_app()
    web.run_app(app, host=host, port=port)
