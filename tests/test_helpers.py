import time
import pytest

from aiozipkin.helpers import (
    TraceContext, make_headers, make_context, make_timestamp,
    filter_none, make_single_header)


@pytest.fixture
def trace_context():
    new_context = TraceContext(
        trace_id='6f9a20b5092fa5e144fd15cc31141cd4',
        parent_id=None,
        span_id='41baf1be2fb9bfc5',
        sampled=True,
        debug=False,
        shared=False)
    return new_context


@pytest.fixture
def other_trace_context():
    context = TraceContext(
        trace_id='6f9a20b5092fa5e144fd15cc31141cd4',
        parent_id='05e3ac9a4f6e3b90',
        span_id='41baf1be2fb9bfc5',
        sampled=None,
        debug=False,
        shared=False)
    return context


def test_make_headers(trace_context):
    headers = make_headers(trace_context)
    expected = {
        'X-B3-Flags': '0',
        'X-B3-Sampled': '1',
        'X-B3-SpanId': '41baf1be2fb9bfc5',
        'X-B3-TraceId': '6f9a20b5092fa5e144fd15cc31141cd4'}
    headers2 = trace_context.make_headers()
    assert headers == expected == headers2


def test_make_single_header(trace_context, other_trace_context):
    headers = make_single_header(trace_context)
    expected = {'b3':  '6f9a20b5092fa5e144fd15cc31141cd4-41baf1be2fb9bfc5-1'}
    headers2 = trace_context.make_single_header()
    assert headers == expected == headers2

    headers = make_single_header(other_trace_context)
    h = '6f9a20b5092fa5e144fd15cc31141cd4-41baf1be2fb9bfc5-d-05e3ac9a4f6e3b90'
    headers2 = other_trace_context.make_single_header()
    expected = {'b3': h}
    assert headers == expected == headers2

    new_context = trace_context._replace(debug=True, sampled=None)
    headers = make_single_header(new_context)
    expected = {'b3':  '6f9a20b5092fa5e144fd15cc31141cd4-41baf1be2fb9bfc5-1'}
    assert headers == expected


def test_make_context(trace_context):
    headers = make_headers(trace_context)
    context = make_context(headers)
    assert trace_context == context

    context = make_context({})
    assert context is None


def test_make_context_single_header(trace_context, other_trace_context):
    headers = make_single_header(trace_context)
    context = make_context(headers)
    assert trace_context == context

    headers = make_single_header(other_trace_context)
    context = make_context(headers)
    assert other_trace_context == context

    headers = {'b3': '0'}
    context = make_context(headers)
    assert context is None

    headers = {'b3': '6f9a20b5092fa5e144fd15cc31141cd4'}
    context = make_context(headers)
    assert context is None


def test_make_timestamp():
    ts = make_timestamp()
    assert len(str(ts)) == 16

    ts = make_timestamp(time.time())
    assert len(str(ts)) == 16


def test_filter_none():
    r = filter_none({'a': 1, 'b': None})
    assert r == {'a': 1}

    r = filter_none({'a': 1, 'b': None, 'c': None}, keys=['a', 'c'])
    assert r == {'a': 1, 'b': None}

    r = filter_none({}, keys=['a', 'c'])
    assert r == {}

    r = filter_none({'a': 1, 'b': None, 'c': {'c': None}}, keys=['a', 'c'])
    assert r == {'a': 1, 'b': None, 'c': {'c': None}}
