from aiozipkin.helpers import create_endpoint
from aiozipkin.sampler import Sampler
from aiozipkin.tracer import Tracer
from aiozipkin.transport import Transport

import pytest


@pytest.fixture
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
