from types import SimpleNamespace
from typing import Any

import aiohttp
import pytest
from aiohttp import web

import aiozipkin as az


async def handler(request: web.Request) -> web.StreamResponse:
    span = az.request_span(request)
    session = request.app["session"]

    url = "https://httpbin.org/get"
    ctx = {"span_context": span.context}
    resp = await session.get(url, trace_request_ctx=ctx)
    data = await resp.text()
    return web.Response(body=data)


async def error_handler(request: web.Request) -> web.StreamResponse:
    span = az.request_span(request)
    session = request.app["session"]

    url = "http://4c2a7f53-9468-43a5-9c7d-466591eda953"
    ctx = {"span_context": span.context}
    await session.get(url, trace_request_ctx=ctx)
    return web.Response(body=b"")


@pytest.fixture
async def client(aiohttp_client: Any, tracer: az.Tracer) -> Any:
    app = web.Application()
    app.router.add_get("/simple", handler)
    app.router.add_get("/error", error_handler)

    trace_config = az.make_trace_config(tracer)
    session = aiohttp.ClientSession(trace_configs=[trace_config])
    app["session"] = session

    az.setup(app, tracer)
    c = await aiohttp_client(app)
    yield c

    await session.close()


@pytest.mark.asyncio
async def test_handler_with_client_signals(
    client: aiohttp.ClientSession, fake_transport: Any
) -> None:
    resp = await client.get("/simple")
    assert resp.status == 200

    assert len(fake_transport.records) == 2

    record1 = fake_transport.records[0].asdict()
    record2 = fake_transport.records[1].asdict()
    assert record1["parentId"] == record2["id"]
    assert record2["tags"]["http.status_code"] == "200"


@pytest.mark.asyncio
async def test_handler_with_client_signals_error(
    client: aiohttp.ClientSession, fake_transport: Any
) -> None:
    resp = await client.get("/error")
    assert resp.status == 500

    assert len(fake_transport.records) == 2
    record1 = fake_transport.records[0].asdict()
    record2 = fake_transport.records[1].asdict()
    assert record1["parentId"] == record2["id"]

    msg = "Cannot connect to host"
    assert msg in record1["tags"]["error"]


@pytest.mark.asyncio
async def test_client_signals(tracer: az.Tracer, fake_transport: Any) -> None:
    trace_config = az.make_trace_config(tracer)
    session = aiohttp.ClientSession(trace_configs=[trace_config])

    with tracer.new_trace() as span:
        span.name("client:signals")
        url = "https://httpbin.org/get"
        # do not propagate headers
        ctx = {"span_context": span.context, "propagate_headers": False}
        resp = await session.get(url, trace_request_ctx=ctx)
        data = await resp.read()
        assert len(data) > 0
        assert az.make_context(resp.request_info.headers) is None

        ctx_ns = SimpleNamespace(span_context=span.context, propagate_headers=False)
        resp = await session.get(url, trace_request_ctx=ctx_ns)
        data = await resp.read()
        assert len(data) > 0
        assert az.make_context(resp.request_info.headers) is None

        # by default headers added
        ctx = {"span_context": span.context}
        resp = await session.get(url, trace_request_ctx=ctx)
        await resp.text()
        assert len(data) > 0
        context = az.make_context(resp.request_info.headers)
        assert context is not None
        assert context.trace_id == span.context.trace_id

    await session.close()

    assert len(fake_transport.records) == 4
    record1 = fake_transport.records[0].asdict()
    record2 = fake_transport.records[1].asdict()
    record3 = fake_transport.records[2].asdict()
    record4 = fake_transport.records[3].asdict()
    assert record3["parentId"] == record4["id"]
    assert record2["parentId"] == record4["id"]
    assert record1["parentId"] == record4["id"]
    assert record4["name"] == "client:signals"


@pytest.mark.asyncio
async def test_client_signals_no_span(tracer: az.Tracer, fake_transport: Any) -> None:
    trace_config = az.make_trace_config(tracer)
    session = aiohttp.ClientSession(trace_configs=[trace_config])

    url = "https://httpbin.org/get"
    resp = await session.get(url)
    data = await resp.read()
    assert len(data) > 0
    await session.close()
    assert len(fake_transport.records) == 0
