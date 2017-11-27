from unittest.mock import patch, MagicMock

from aiohttp.web_exceptions import HTTPNotFound, HTTPException
from pytest import raises

import aiozipkin as az
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from aiozipkin.aiohttp_helpers import middleware_maker
from unittest import mock

import pytest


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


def test_basic_setup(tracer):
    app = web.Application()
    az.setup(app, tracer)

    fetched_tracer = az.get_tracer(app)
    assert len(app.middlewares) == 1
    assert tracer is fetched_tracer


@pytest.mark.asyncio
async def test_middleware_with_default_transport(tracer, fake_transport):
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


valid_ips = [
    ('ipv4', '127.0.0.1', None),
    ('ipv4', '10.2.14.10', None),
    ('ipv4', '255.255.255.1', None),
    ('ipv6', '::1', None),
    ('ipv6', '2001:cdba:0000:0000::0000:3257:9652', '2001:cdba::3257:9652'),
    ('ipv6', '2001:cdba:0:0:0:0:3257:9652', '2001:cdba::3257:9652'),
    ('ipv6', '2001:cdba::3257:9652', None),
    ('ipv6', 'fec0::', None),
]


@pytest.mark.asyncio
@pytest.mark.parametrize('version,address_in,address_out', valid_ips)
async def test_middleware_with_valid_ip(tracer, version,
                                        address_in, address_out):
    if address_out is None:
        address_out = address_in

    app = web.Application()
    az.setup(app, tracer)

    # Fake transport
    transp = mock.Mock()
    transp.get_extra_info.return_value = (address_in, '0')

    async def handler(request):
        return web.Response(body=b'data')

    req = make_mocked_request('GET', '/',
                              headers={'token': 'x'},
                              transport=transp)

    middleware_factory = middleware_maker()
    middleware = await middleware_factory(app, handler)
    with patch('aiozipkin.span.Span.remote_endpoint') as mocked_remote_ep:
        await middleware(req)

        assert mocked_remote_ep.call_count == 1
        args, kwargs = mocked_remote_ep.call_args
        assert kwargs[version] == address_out


invalid_ips = [
    ('ipv4', '127.a.b.1'),
    ('ipv4', '.2.14.10'),
    ('ipv4', '256.255.255.1'),
    ('ipv4', 'invalid'),
    ('ipv6', ':::'),
    ('ipv6', '10000:cdba:0000:0000:0000:0000:3257:9652'),
    ('ipv6', '2001:cdba:g:0:0:0:3257:9652'),
    ('ipv6', '2001:cdba::3257:9652:'),
    ('ipv6', 'invalid'),
]


@pytest.mark.asyncio
@pytest.mark.parametrize('version,address', invalid_ips)
async def test_middleware_with_invalid_ip(tracer, version, address):
    app = web.Application()
    az.setup(app, tracer)

    # Fake transport
    transp = mock.Mock()
    transp.get_extra_info.return_value = (address, '0')

    async def handler(request):
        return web.Response(body=b'data')

    req = make_mocked_request('GET', '/',
                              headers={'token': 'x'},
                              transport=transp)

    middleware_factory = middleware_maker()
    middleware = await middleware_factory(app, handler)
    with patch('aiozipkin.span.Span.remote_endpoint') as mocked_remote_ep:
        await middleware(req)

        assert mocked_remote_ep.call_count == 0


@pytest.mark.asyncio
async def test_middleware_with_handler_404(tracer):
    app = web.Application()
    az.setup(app, tracer)

    async def handler(request):
        raise HTTPNotFound

    req = make_mocked_request('GET', '/', headers={'token': 'x'})

    middleware_factory = middleware_maker()
    middleware = await middleware_factory(app, handler)

    with raises(HTTPException):
        await middleware(req)


@pytest.mark.asyncio
async def test_middleware_cleanup_app(tracer):
    tracer.close = AsyncMock()
    app = web.Application()
    az.setup(app, tracer)
    await app.cleanup()
    assert tracer.close.call_count == 1
