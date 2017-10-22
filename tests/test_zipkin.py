import asyncio

import aiohttp
import aiozipkin as az
from yarl import URL

import pytest
from async_generator import yield_, async_generator


@pytest.fixture
@async_generator
async def client(loop):
    async with aiohttp.ClientSession(loop=loop) as client:
        await yield_(client)


@pytest.mark.asyncio
async def test_basic(zipkin_url, client, loop):
    endpoint = az.create_endpoint('simple_service', ipv4='127.0.0.1', port=80)
    interval = 50
    tracer = az.create(zipkin_url, endpoint, sample_rate=1.0,
                       send_inteval=interval, loop=loop)

    with tracer.new_trace(sampled=True) as span:
        span.name('root_span')
        span.tag('span_type', 'root')
        span.kind(az.CLIENT)
        span.annotate('SELECT * FROM')
        await asyncio.sleep(0.1)
        span.annotate('start end sql')

    # close forced sending data to server regardless of send interval
    await tracer.close()
    # give zipkin time to process maessage :((
    await asyncio.sleep(1)

    trace_id = span.context.trace_id
    url = URL(zipkin_url).with_path('/zipkin/api/v1/traces')
    resp = await client.get(url)
    data = await resp.json()
    assert any(s['traceId'] == trace_id for trace in data for s in trace)


@pytest.mark.asyncio
async def test_exception_in_span(zipkin_url, client, loop):
    endpoint = az.create_endpoint('error_service', ipv4='127.0.0.1', port=80)
    interval = 50
    tracer = az.create(zipkin_url, endpoint, send_inteval=interval, loop=loop)

    def func(span):
        with span:
            span.name('root_span')
            raise RuntimeError('foo')

    span = tracer.new_trace(sampled=True)
    with pytest.raises(RuntimeError):
        func(span)

    await tracer.close()
    # give zipkin time to process maessage :((
    await asyncio.sleep(1)

    url = URL(zipkin_url).with_path('/zipkin/api/v1/traces')
    resp = await client.get(url)
    data = await resp.json()

    expected = {
        'endpoint': {
            'ipv4': '127.0.0.1',
            'port': 80,
            'serviceName': 'error_service'},
        'key': 'error',
        'value': 'foo'
    }

    assert any(expected in s['binaryAnnotations']
               for trace in data for s in trace)
