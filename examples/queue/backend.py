import asyncio

import aiojobs.aiohttp
from aiohttp import web

import aiozipkin as az


async def consume_message(message, tracer):
    await asyncio.sleep(0.1)
    headers = message.get("headers", None)
    context = az.make_context(headers)

    with tracer.new_child(context) as span_consumer:
        span_consumer.name("consumer event")
        span_consumer.remote_endpoint("broker", ipv4="127.0.0.1", port=9011)
        span_consumer.kind(az.CONSUMER)

    with tracer.new_child(span_consumer.context) as span_worker:
        span_worker.name("process event")
        await asyncio.sleep(0.1)


async def handler(request):
    message = await request.json()
    tracer = az.get_tracer(request.app)
    for _ in range(5):
        asyncio.ensure_future(
            aiojobs.aiohttp.spawn(request, consume_message(message, tracer))
        )

    return web.Response(text="ok")


async def make_app(host, port):
    app = web.Application()
    app.router.add_post("/consume", handler)
    aiojobs.aiohttp.setup(app)

    zipkin_address = "http://127.0.0.1:9411/api/v2/spans"
    endpoint = az.create_endpoint("backend_broker", ipv4=host, port=port)
    tracer = await az.create(zipkin_address, endpoint, sample_rate=1.0)
    az.setup(app, tracer)
    return app


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 9011
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(make_app(host, port))
    web.run_app(app, host=host, port=port)
