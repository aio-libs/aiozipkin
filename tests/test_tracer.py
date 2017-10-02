import pytest
from unittest import mock

from aiozipkin.helpers import create_endpoint
from aiozipkin.sampler import Sampler
from aiozipkin.tracer import Tracer
from aiozipkin.transport import Transport


class FakeTransport(Transport):

    def __init__(self):
        self.records = []

    def send(self, record):
        self.records.append(record)


@pytest.fixture
def fake_transport():
    transport = FakeTransport()
    return transport


@pytest.fixture
def tracer(fake_transport):
    sampler = Sampler(sample_rate=1.0)
    endpoint = create_endpoint("test_service", ipv4="127.0.0.1", port=8080)
    return Tracer(fake_transport, sampler, endpoint)


def test_basic(tracer, fake_transport):
    with tracer.new_trace() as span:
        span.name("root_span")
        span.tag("span_type", "root")
        span.kind("CLIENT")
        span.annotate("start:sql", ts=1506970524)
        span.annotate("end:sql", ts=1506970524)

    assert len(fake_transport.records) == 1
    record = fake_transport.records[0]
    expected = {
        'annotations': [{'timestamp': 1506970524000000, 'value': 'start:sql'},
                        {'timestamp': 1506970524000000, 'value': 'end:sql'}],
        'debug': False,
        'duration': mock.ANY,
        'id': mock.ANY,
        'kind': 'CLIENT',
        'localEndpoint': {'serviceName': 'test_service',
                          'ipv4': '127.0.0.1',
                          'ipv6': None,
                          'port': 8080},
        'name': 'root_span',
        'parentId': None,
        'remoteEndpoint': None,
        'shared': False,
        'tags': {'span_type': 'root'},
        'timestamp': mock.ANY,
        'traceId': mock.ANY}
    assert record.asdict() == expected
