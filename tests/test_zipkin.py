import asyncio
import gc
import logging
import tracemalloc
from typing import Any, Union

import aiohttp
import pytest
from yarl import URL

import aiozipkin as az


async def _retry_zipkin_client(
    url: Union[str, URL],
    client: aiohttp.ClientSession,
    retries: int = 5,
    backoff_time: int = 1,
) -> Any:
    tries = 0
    while tries < retries:
        await asyncio.sleep(backoff_time)
        resp = await client.get(url)
        if resp.status > 200:
            tries += 1
            continue
        data = await resp.json()
        return data
    raise RuntimeError("Unreachable")


@pytest.mark.asyncio  # type: ignore[misc]
async def test_basic(
    zipkin_url: str, client: aiohttp.ClientSession, loop: asyncio.AbstractEventLoop
) -> None:
    endpoint = az.create_endpoint("simple_service", ipv4="127.0.0.1", port=80)
    interval = 50
    tracer = await az.create(
        zipkin_url,
        endpoint,
        sample_rate=1.0,
        send_interval=interval,
    )

    with tracer.new_trace(sampled=True) as span:
        span.name("root_span")
        span.tag("span_type", "root")
        span.kind(az.CLIENT)
        span.annotate("SELECT * FROM")
        await asyncio.sleep(0.1)
        span.annotate("start end sql")

    # close forced sending data to server regardless of send interval
    await tracer.close()

    trace_id = span.context.trace_id
    url = URL(zipkin_url).with_path("/zipkin/api/v2/traces")
    data = await _retry_zipkin_client(url, client)
    assert any(s["traceId"] == trace_id for trace in data for s in trace), data


async def test_basic_context_manager(
    zipkin_url: str, client: aiohttp.ClientSession, loop: asyncio.AbstractEventLoop
) -> None:
    endpoint = az.create_endpoint("simple_service", ipv4="127.0.0.1", port=80)
    interval = 50
    async with az.create(
        zipkin_url, endpoint, sample_rate=1.0, send_interval=interval
    ) as tracer:
        with tracer.new_trace(sampled=True) as span:
            span.name("root_span")
            await asyncio.sleep(0.1)

    trace_id = span.context.trace_id
    url = URL(zipkin_url).with_path("/zipkin/api/v2/traces")
    data = await _retry_zipkin_client(url, client)

    assert any(s["traceId"] == trace_id for trace in data for s in trace), data


@pytest.mark.asyncio  # type: ignore[misc]
async def test_exception_in_span(
    zipkin_url: str, client: aiohttp.ClientSession, loop: asyncio.AbstractEventLoop
) -> None:
    endpoint = az.create_endpoint("error_service", ipv4="127.0.0.1", port=80)
    interval = 50
    async with az.create(
        zipkin_url,
        endpoint,
        send_interval=interval,
    ) as tracer:

        def func(span: az.SpanAbc) -> None:
            with span:
                span.name("root_span")
                raise RuntimeError("foo")

        span = tracer.new_trace(sampled=True)
        with pytest.raises(RuntimeError):
            func(span)

    url = URL(zipkin_url).with_path("/zipkin/api/v2/traces")
    data = await _retry_zipkin_client(url, client)
    assert any({"error": "foo"} == s.get("tags", {}) for trace in data for s in trace)


@pytest.mark.asyncio  # type: ignore[misc]
async def test_zipkin_error(
    client: aiohttp.ClientSession, loop: asyncio.AbstractEventLoop, caplog: Any
) -> None:
    endpoint = az.create_endpoint("error_service", ipv4="127.0.0.1", port=80)
    interval = 50
    zipkin_url = "https://httpbin.org/status/404"
    async with az.create(
        zipkin_url,
        endpoint,
        sample_rate=1.0,
        send_interval=interval,
    ) as tracer:
        with tracer.new_trace(sampled=True) as span:
            span.kind(az.CLIENT)
            await asyncio.sleep(0.0)

    assert len(caplog.records) == 1
    msg = "zipkin responded with code: "
    assert msg in str(caplog.records[0].exc_info)

    t = ("aiozipkin", logging.ERROR, "Can not send spans to zipkin")
    assert caplog.record_tuples == [t]


@pytest.mark.asyncio  # type: ignore[misc]
async def test_leak_in_transport(
    zipkin_url: str, client: aiohttp.ClientSession, loop: asyncio.AbstractEventLoop
) -> None:

    tracemalloc.start()

    endpoint = az.create_endpoint("simple_service")
    tracer = await az.create(
        zipkin_url,
        endpoint,
        sample_rate=1,
        send_interval=0.0001,
    )

    await asyncio.sleep(5)
    gc.collect()
    snapshot1 = tracemalloc.take_snapshot()

    await asyncio.sleep(10)
    gc.collect()
    snapshot2 = tracemalloc.take_snapshot()

    top_stats = snapshot2.compare_to(snapshot1, "lineno")
    count = sum(s.count for s in top_stats)
    await tracer.close()
    assert count < 400  # in case of leak this number is around 901452
