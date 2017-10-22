import aiozipkin as az
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from aiozipkin.aiohttp_helpers import middleware_maker

import pytest


def test_basic_setup(tracer):
    app = web.Application()
    az.setup(app, tracer)

    fetched_tracer = az.get_tracer(app)
    assert len(app.middlewares) == 1
    assert tracer is fetched_tracer


@pytest.mark.asyncio
async def test_middleware(tracer, fake_transport):
    app = web.Application()
    az.setup(app, tracer)

    async def handler(request):
        return web.Response(body=b'data')
    req = make_mocked_request('GET', '/', headers={'token': 'x'})

    middleware_factory = middleware_maker()

    middleware = await middleware_factory(app, handler)
    await middleware(req)
    span = az.request_span(req)
    assert span
    assert len(fake_transport.records) == 1

    # noop span does not produce records
    headers = {'X-B3-Sampled': '0'}
    req_noop = make_mocked_request('GET', '/', headers=headers)
    await middleware(req_noop)
    span = az.request_span(req_noop)
    assert span
    assert len(fake_transport.records) == 1
