import asyncio
import gc

from aiozipkin.helpers import create_endpoint, TraceContext
from aiozipkin.sampler import Sampler
from aiozipkin.tracer import Tracer
from aiozipkin.transport import Transport

import pytest


@pytest.fixture(scope='session')
def event_loop():
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    gc.collect()
    loop.close()


@pytest.fixture(scope='session')
def loop(event_loop):
    return event_loop


class FakeTransport(Transport):

    def __init__(self):
        self.records = []

    def send(self, record):
        self.records.append(record)


@pytest.fixture
def fake_transport():
    transport = FakeTransport()
    return transport


@pytest.fixture(name="tracer")
def tracer_fixture(fake_transport):
    sampler = Sampler(sample_rate=1.0)
    endpoint = create_endpoint("test_service", ipv4="127.0.0.1", port=8080)
    return Tracer(fake_transport, sampler, endpoint)


@pytest.fixture
def context():
    context = TraceContext(
        trace_id="6f9a20b5092fa5e144fd15cc31141cd4",
        parent_id=None,
        span_id="41baf1be2fb9bfc5",
        sampled=True,
        debug=False,
        shared=True)
    return context


pytest_plugins = ['docker_fixtures']
