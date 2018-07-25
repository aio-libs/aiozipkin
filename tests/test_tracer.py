from unittest import mock

import pytest
from aiozipkin.helpers import (
    TraceContext, create_endpoint,
)
from aiozipkin.tracer import NoopSpan, Span, create, create_custom
from aiozipkin.transport import StubTransport, Transport
from aiozipkin.sampler import SamplerABC


def test_basic(tracer, fake_transport):
    with tracer.new_trace() as span:
        span.name('root_span')
        span.tag('span_type', 'root')
        span.kind('CLIENT')
        span.annotate('start:sql', ts=1506970524)
        span.annotate('end:sql', ts=1506970524)
        span.remote_endpoint('service_a', ipv4='127.0.0.1', port=8080)

    assert not span.is_noop
    assert span.tracer is tracer
    assert span.context.parent_id is None
    assert isinstance(span, Span)
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
                          'port': 8080},
        'name': 'root_span',
        'parentId': None,
        'remoteEndpoint': {'serviceName': 'service_a',
                           'ipv4': '127.0.0.1',
                           'port': 8080},
        'shared': False,
        'tags': {'span_type': 'root'},
        'timestamp': mock.ANY,
        'traceId': mock.ANY}
    assert record.asdict() == expected
    span.finish()
    # make sure double finish does not error
    span.finish()


def test_noop_span_methods(tracer):
    context = TraceContext(
        trace_id='6f9a20b5092fa5e144fd15cc31141cd4',
        parent_id=None,
        span_id='41baf1be2fb9bfc5',
        sampled=False,
        debug=False,
        shared=True)

    with tracer.new_child(context) as span:
        span.name('root_span')
        span.tag('span_type', 'root')
        span.kind('CLIENT')
        span.annotate('start:sql', ts=1506970524)
        span.annotate('end:sql', ts=1506970524)
        span.remote_endpoint('service_a', ipv4='127.0.0.1', port=8080)

        with span.new_child() as child_span:
            pass

    assert isinstance(span, NoopSpan)
    assert span.context.parent_id is not None
    assert not span.context.sampled
    assert span.is_noop

    span = tracer.to_span(context)
    assert isinstance(span, NoopSpan)
    assert span.tracer is tracer

    assert isinstance(child_span, NoopSpan)


def test_trace_join_span(tracer, context):

    with tracer.join_span(context) as span:
        span.name('name')

    assert span.context.trace_id == context.trace_id
    assert span.context.span_id == context.span_id
    assert span.context.parent_id is None

    new_context = context._replace(sampled=None)
    with tracer.join_span(new_context) as span:
        span.name('name')

    assert span.context.sampled is not None


def test_trace_new_child(tracer, context):

    with tracer.new_child(context) as span:
        span.name('name')

    assert span.context.trace_id == context.trace_id
    assert span.context.parent_id == context.span_id
    assert span.context.span_id is not None


def test_span_new_child(tracer, context, fake_transport):

    with tracer.new_child(context) as span:
        span.name('name')
        with span.new_child('child', 'CLIENT') as child_span1:
            pass
        with span.new_child() as child_span2:
            pass

    assert span.context.trace_id == child_span1.context.trace_id
    assert span.context.span_id == child_span1.context.parent_id
    assert span.context.trace_id == child_span2.context.trace_id
    assert span.context.span_id == child_span2.context.parent_id

    record = fake_transport.records[0]
    data = record.asdict()
    assert data['name'] == 'child'
    assert data['kind'] == 'CLIENT'

    record = fake_transport.records[1]
    data = record.asdict()
    assert data['name'] == 'unknown'
    assert 'kind' not in data


def test_error(tracer, fake_transport):
    def func():
        with tracer.new_trace() as span:
            span.name('root_span')
            raise RuntimeError('boom')

    with pytest.raises(RuntimeError):
        func()

    assert len(fake_transport.records) == 1
    record = fake_transport.records[0]

    data = record.asdict()
    assert data['tags'] == {'error': 'boom'}


def test_null_annotation(tracer, fake_transport):
    with tracer.new_trace() as span:
        span.annotate(None, ts=1506970524)

    assert len(fake_transport.records) == 1
    record = fake_transport.records[0]
    assert record.asdict()['annotations'][0]['value'] == 'None'


@pytest.mark.asyncio
async def test_create_transport():
    endpoint = create_endpoint('test_service', ipv4='127.0.0.1', port=8080)
    with mock.patch(
            'aiozipkin.tracer.Tracer') as tracer_stub:  # type: mock.MagicMock
        await create('', endpoint)
        assert isinstance(tracer_stub.call_args[0][0], StubTransport)

        with mock.patch('aiozipkin.tracer.Transport.__init__') as init_mock:
            init_mock.return_value = None
            await create('sample.endpoint', endpoint)
            assert isinstance(tracer_stub.call_args[0][0], Transport)


@pytest.mark.asyncio
async def test_create_custom(fake_transport):
    endpoint = create_endpoint('test_service', ipv4='127.0.0.1', port=8080)

    class FakeSampler(SamplerABC):
        def is_sampled(self, trace_id: str):
            return True
    with mock.patch(
            'aiozipkin.tracer.Tracer') as tracer_stub:  # type: mock.MagicMock
        await create_custom(fake_transport, FakeSampler(), endpoint)
        assert isinstance(tracer_stub.call_args[0][0], StubTransport)
        assert isinstance(tracer_stub.call_args[0][1], FakeSampler)
