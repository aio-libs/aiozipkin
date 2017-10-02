import time
from collections import namedtuple


CLIENT = "CLIENT"
SERVER = "SERVER"
PRODUCER = "PRODUCER"
CONSUMER = "CONSUMER"


CLIENT_SEND = "cs"
SERVER_SEND = "ss"
CLIENT_RECEIVED = "cr"
SERVER_RECEIVED = "sr"


TRACE_ID_HEADER = 'X-B3-TraceId'
SPAN_ID_HEADER = 'X-B3-SpanId'
PARENT_ID_HEADER = 'X-B3-ParentSpanId'
FLAGS_HEADER = 'X-B3-Flags'
SAMPLED_ID_HEADER = 'X-B3-Sampled'


TraceContext = namedtuple(
    'TraceContext', [
        "trace_id",
        "parent_id",
        "span_id",
        "sampled",
        "debug",
        "shared",
        ]
)

Endpoint = namedtuple(
    'Endpoint', ["serviceName", "ipv4", "ipv6", "port"]
)


def create_endpoint(servce_name, *, ipv4=None, ipv6=None, port=None):
    return Endpoint(servce_name, ipv4, ipv6, port)


def make_timestamp(ts=None):
    ts = ts if ts is not None else time.time()
    return int(ts * 1000 * 1000)  # microseconds


def make_headers(context):
    headers = {
        TRACE_ID_HEADER: context.trace_id,
        SPAN_ID_HEADER: context.span_id,
        PARENT_ID_HEADER: context.parent_id,
        FLAGS_HEADER: '0',
        SAMPLED_ID_HEADER: '1' if context.sampled else '0',
    }
    return headers


_required_headers = (TRACE_ID_HEADER, PARENT_ID_HEADER, SPAN_ID_HEADER)


def _parse_sampled(headers):
    sampled = headers.get(SAMPLED_ID_HEADER, None)
    if sampled is None or sampled == "":
        return None
    # TODO: add more test cases
    return True if sampled == '1' else False


def make_context(headers):
    # TODO: add validation for trace_id/span_id/parent_id

    if not all(h in headers for h in _required_headers):
        return None

    context = TraceContext(
        trace_id=headers.get(TRACE_ID_HEADER),
        parent_id=headers.get(PARENT_ID_HEADER),
        span_id=headers.get(SPAN_ID_HEADER),
        sampled=_parse_sampled(headers),
        shared=True,
        debug=True if headers.get(FLAGS_HEADER, '0') == '1' else False
    )
    return context
