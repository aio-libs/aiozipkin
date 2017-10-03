import pytest

from aiozipkin.helpers import TraceContext, make_headers, make_context


@pytest.fixture
def trace_context():
    new_context = TraceContext(
        trace_id="6f9a20b5092fa5e144fd15cc31141cd4",
        parent_id=None,
        span_id="41baf1be2fb9bfc5",
        sampled=True,
        debug=False,
        shared=True)
    return new_context


def test_make_headers(trace_context):
    headers = make_headers(trace_context)
    expected = {
        'X-B3-Flags': '0',
        'X-B3-Sampled': '1',
        'X-B3-SpanId': '41baf1be2fb9bfc5',
        'X-B3-TraceId': '6f9a20b5092fa5e144fd15cc31141cd4'}
    assert headers == expected


def test_make_context(trace_context):
    headers = make_headers(trace_context)
    headers = {
        'X-B3-Flags': '0',
        'X-B3-ParentSpanId': None,
        'X-B3-Sampled': '1',
        'X-B3-SpanId': '41baf1be2fb9bfc5',
        'X-B3-TraceId': '6f9a20b5092fa5e144fd15cc31141cd4'}
    expected = make_context(headers)
    assert trace_context == expected
