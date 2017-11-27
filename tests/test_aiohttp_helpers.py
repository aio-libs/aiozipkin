import aiozipkin as az
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from aiozipkin.aiohttp_helpers import middleware_maker
from unittest import mock

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

    # Fake transport, with IPv4
    transp = mock.Mock()
    transp.get_extra_info.return_value = ('127.0.0.1', '0')

    async def handler(request):
        return web.Response(body=b'data')
    req = make_mocked_request('GET', '/',
                              headers={'token': 'x'},
                              transport=transp)

    middleware_factory = middleware_maker()

    middleware = await middleware_factory(app, handler)
    await middleware(req)
    span = az.request_span(req)
    assert span
    assert span._record._remote_endpoint['ipv4'] == '127.0.0.1'
    assert len(fake_transport.records) == 1

    # Same with IPv6
    transp.get_extra_info.return_value = ('::1', '0')
    req = make_mocked_request('GET', '/',
                              headers={'token': 'x'},
                              transport=transp)
    middleware = await middleware_factory(app, handler)
    await middleware(req)
    span = az.request_span(req)
    assert span._record._remote_endpoint['ipv6'] == '::1'

    # noop span does not produce records
    headers = {'X-B3-Sampled': '0'}
    req_noop = make_mocked_request('GET', '/', headers=headers)
    await middleware(req_noop)
    span = az.request_span(req_noop)
    assert span
    assert len(fake_transport.records) == 2
