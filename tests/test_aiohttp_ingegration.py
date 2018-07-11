import aiohttp

import aiozipkin as az
import pytest

from aiohttp import web
from async_generator import yield_, async_generator


async def handler(request):
    span = az.request_span(request)
    session = request.app['session']

    url = 'https://httpbin.org/get'
    ctx = {'span_context': span.context}
    resp = await session.get(url, trace_request_ctx=ctx)
    data = await resp.text()
    return web.Response(body=data)


async def error_handler(request):
    span = az.request_span(request)
    session = request.app['session']

    url = 'http://4c2a7f53-9468-43a5-9c7d-466591eda953'
    ctx = {'span_context': span.context}
    await session.get(url, trace_request_ctx=ctx)
    return web.Response(body=b'')


@pytest.fixture
@async_generator
async def client(test_client, tracer):
    app = web.Application()
    app.router.add_get('/simple', handler)
    app.router.add_get('/error', error_handler)

    trace_config = az.make_trace_config(tracer)
    session = aiohttp.ClientSession(trace_configs=[trace_config])
    app['session'] = session

    az.setup(app, tracer)
    c = await test_client(app)
    await yield_(c)

    await session.close()


@pytest.mark.asyncio
async def test_handler_with_client_signals(client, fake_transport):
    resp = await client.get('/simple')
    assert resp.status == 200

    assert len(fake_transport.records) == 2

    record1 = fake_transport.records[0].asdict()
    record2 = fake_transport.records[1].asdict()
    assert record1['parentId'] == record2['id']
    assert record2['tags']['http.status_code'] == '200'


@pytest.mark.asyncio
async def test_handler_with_client_signals_error(client, fake_transport):
    resp = await client.get('/error')
    assert resp.status == 500

    assert len(fake_transport.records) == 2
    record1 = fake_transport.records[0].asdict()
    record2 = fake_transport.records[1].asdict()
    assert record1['parentId'] == record2['id']

    msg = 'Cannot connect to host'
    assert msg in record1['tags']['error']


@pytest.mark.asyncio
async def test_client_signals(tracer, fake_transport):
    trace_config = az.make_trace_config(tracer)
    session = aiohttp.ClientSession(trace_configs=[trace_config])

    with tracer.new_trace() as span:
        span.name('client:signals')
        url = 'https://httpbin.org/get'
        # do not propagate headers
        ctx = {'span_context': span.context, 'propagate_headers': False}
        resp = await session.get(url, trace_request_ctx=ctx)
        data = await resp.read()
        assert len(data) > 0
        assert az.make_context(resp.request_info.headers) is None

        # by default headers added
        ctx = {'span_context': span.context}
        resp = await session.get(url, trace_request_ctx=ctx)
        await resp.text()
        assert len(data) > 0
        context = az.make_context(resp.request_info.headers)
        assert context.trace_id == span.context.trace_id

    await session.close()

    assert len(fake_transport.records) == 3
    record1 = fake_transport.records[0].asdict()
    record2 = fake_transport.records[1].asdict()
    record3 = fake_transport.records[2].asdict()
    assert record2['parentId'] == record3['id']
    assert record1['parentId'] == record3['id']
    assert record3['name'] == 'client:signals'


@pytest.mark.asyncio
async def test_client_signals_no_span(tracer, fake_transport):
    trace_config = az.make_trace_config(tracer)
    session = aiohttp.ClientSession(trace_configs=[trace_config])

    url = 'https://httpbin.org/get'
    resp = await session.get(url)
    data = await resp.read()
    assert len(data) > 0
    await session.close()
    assert len(fake_transport.records) == 0
