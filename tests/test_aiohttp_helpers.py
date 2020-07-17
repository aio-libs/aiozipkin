import asyncio
from typing import Any, Optional
from unittest.mock import Mock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from aiohttp.web_exceptions import HTTPException, HTTPNotFound

import aiozipkin as az
from aiozipkin.aiohttp_helpers import middleware_maker


def test_basic_setup(tracer: az.Tracer) -> None:
    app = web.Application()
    az.setup(app, tracer)

    fetched_tracer = az.get_tracer(app)
    assert len(app.middlewares) == 1
    assert tracer is fetched_tracer


@pytest.mark.asyncio  # type: ignore[misc]
async def test_middleware_with_default_transport(
    tracer: az.Tracer, fake_transport: Any
) -> None:
    app = web.Application()
    az.setup(app, tracer)

    async def handler(request: web.Request) -> web.StreamResponse:
        return web.Response(body=b"data")

    req = make_mocked_request("GET", "/aa", headers={"token": "x"}, app=app)
    req.match_info.route.resource.canonical = "/{pid}"

    middleware = middleware_maker()
    await middleware(req, handler)
    span = az.request_span(req)
    assert span
    assert len(fake_transport.records) == 1

    rec = fake_transport.records[0]
    assert rec.asdict()["tags"][az.HTTP_ROUTE] == "/{pid}"

    # noop span does not produce records
    headers = {"X-B3-Sampled": "0"}
    req_noop = make_mocked_request("GET", "/", headers=headers, app=app)
    await middleware(req_noop, handler)
    span = az.request_span(req_noop)
    assert span
    assert len(fake_transport.records) == 1


@pytest.mark.asyncio  # type: ignore[misc]
async def test_middleware_with_not_skip_route(
    tracer: az.Tracer, fake_transport: Any
) -> None:
    async def handler(request: web.Request) -> web.StreamResponse:
        return web.Response(body=b"data")

    app = web.Application()
    skip_route = app.router.add_get("/", handler)
    az.setup(app, tracer)

    match_info = Mock()
    match_info.route = skip_route

    req = make_mocked_request("GET", "/", headers={"token": "x"}, app=app)
    req._match_info = match_info
    middleware = middleware_maker(skip_routes=[skip_route])
    await middleware(req, handler)

    assert len(fake_transport.records) == 0


valid_ips = [
    ("ipv4", "127.0.0.1", None),
    ("ipv4", "10.2.14.10", None),
    ("ipv4", "255.255.255.1", None),
    ("ipv6", "::1", None),
    ("ipv6", "2001:cdba:0000:0000::0000:3257:9652", "2001:cdba::3257:9652"),
    ("ipv6", "2001:cdba:0:0:0:0:3257:9652", "2001:cdba::3257:9652"),
    ("ipv6", "2001:cdba::3257:9652", None),
    ("ipv6", "fec0::", None),
]


@pytest.mark.asyncio  # type: ignore[misc]
@pytest.mark.parametrize("version,address_in,address_out", valid_ips)  # type: ignore[misc]  # noqa
async def test_middleware_with_valid_ip(
    tracer: az.Tracer, version: str, address_in: str, address_out: Optional[str]
) -> None:
    if address_out is None:
        address_out = address_in

    app = web.Application()
    az.setup(app, tracer)

    # Fake transport
    transp = Mock()
    transp.get_extra_info.return_value = (address_in, "0")

    async def handler(request: web.Request) -> web.StreamResponse:
        return web.Response(body=b"data")

    req = make_mocked_request(
        "GET", "/", headers={"token": "x"}, transport=transp, app=app
    )

    middleware = middleware_maker()
    with patch("aiozipkin.span.Span.remote_endpoint") as mocked_remote_ep:
        await middleware(req, handler)

        assert mocked_remote_ep.call_count == 1
        args, kwargs = mocked_remote_ep.call_args
        assert kwargs[version] == address_out


invalid_ips = [
    ("ipv4", "127.a.b.1"),
    ("ipv4", ".2.14.10"),
    ("ipv4", "256.255.255.1"),
    ("ipv4", "invalid"),
    ("ipv6", ":::"),
    ("ipv6", "10000:cdba:0000:0000:0000:0000:3257:9652"),
    ("ipv6", "2001:cdba:g:0:0:0:3257:9652"),
    ("ipv6", "2001:cdba::3257:9652:"),
    ("ipv6", "invalid"),
]


@pytest.mark.asyncio  # type: ignore[misc]
@pytest.mark.parametrize("version,address", invalid_ips)  # type: ignore[misc]
async def test_middleware_with_invalid_ip(
    tracer: az.Tracer, version: str, address: str
) -> None:
    app = web.Application()
    az.setup(app, tracer)

    # Fake transport
    transp = Mock()
    transp.get_extra_info.return_value = (address, "0")

    async def handler(request: web.Request) -> web.StreamResponse:
        return web.Response(body=b"data")

    req = make_mocked_request(
        "GET", "/", headers={"token": "x"}, transport=transp, app=app
    )

    middleware = middleware_maker()
    with patch("aiozipkin.span.Span.remote_endpoint") as mocked_remote_ep:
        await middleware(req, handler)
        assert mocked_remote_ep.call_count == 0


@pytest.mark.asyncio  # type: ignore[misc]
async def test_middleware_with_handler_404(tracer: az.Tracer) -> None:
    app = web.Application()
    az.setup(app, tracer)

    async def handler(request: web.Request) -> web.StreamResponse:
        raise HTTPNotFound

    req = make_mocked_request("GET", "/", headers={"token": "x"}, app=app)

    middleware = middleware_maker()

    with pytest.raises(HTTPException):
        await middleware(req, handler)


@pytest.mark.asyncio  # type: ignore[misc]
async def test_middleware_cleanup_app(tracer: az.Tracer) -> None:
    fut: asyncio.Future[None] = asyncio.Future()
    fut.set_result(None)
    with patch.object(tracer, "close", return_value=fut) as mocked_close:
        app = web.Application()
        az.setup(app, tracer)
        app.freeze()
        await app.cleanup()
        assert mocked_close.call_count == 1
