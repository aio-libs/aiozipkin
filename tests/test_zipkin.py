import asyncio

import aiohttp
import aiozipkin as az
from yarl import URL

import pytest


@pytest.fixture
async def session(loop):
    async with aiohttp.ClientSession(loop=loop) as client:
        yield client


@pytest.mark.asyncio
async def test_basic(zipkin_url, session, loop):
    endpoint = az.create_endpoint('simple_service', ipv4='127.0.0.1', port=80)
    tracer = az.create(zipkin_url, endpoint, send_inteval=0.5, loop=loop)

    with tracer.new_trace(sampled=True) as span:
        span.name('root_span')
        span.tag('span_type', 'root')
        span.kind(az.CLIENT)
        span.annotate('SELECT * FROM')
        await asyncio.sleep(0.1)
        span.annotate('start end sql')

    await tracer.close()

    trace_id = span.context.trace_id
    url = URL(zipkin_url).with_path("/zipkin/api/v1/traces")
    resp = await session.get(url)
    data = await resp.json()
    assert any(s["traceId"] == trace_id for trace in data for s in trace)
