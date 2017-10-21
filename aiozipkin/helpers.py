import time
from collections import namedtuple

# possible span kinds
CLIENT = 'CLIENT'
SERVER = 'SERVER'
PRODUCER = 'PRODUCER'
CONSUMER = 'CONSUMER'

# reserved annotation names
CLIENT_SEND = 'cs'
SERVER_SEND = 'ss'
CLIENT_RECEIVED = 'cr'
SERVER_RECEIVED = 'sr'


TRACE_ID_HEADER = 'X-B3-TraceId'
SPAN_ID_HEADER = 'X-B3-SpanId'
PARENT_ID_HEADER = 'X-B3-ParentSpanId'
FLAGS_HEADER = 'X-B3-Flags'
SAMPLED_ID_HEADER = 'X-B3-Sampled'


_TraceContext = namedtuple(
    'TraceContext', [
        'trace_id',
        'parent_id',
        'span_id',
        'sampled',
        'debug',
        'shared',
        ]
)


class TraceContext(_TraceContext):

    def make_headers(self):
        return make_headers(self)


Endpoint = namedtuple(
    'Endpoint', ['serviceName', 'ipv4', 'ipv6', 'port']
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
        FLAGS_HEADER: '0',
        SAMPLED_ID_HEADER: '1' if context.sampled else '0',
    }
    if context.parent_id is not None:
        headers[PARENT_ID_HEADER] = context.parent_id
    return headers


def parse_sampled(headers):
    sampled = headers.get(SAMPLED_ID_HEADER.lower(), None)
    if sampled is None or sampled == '':
        return None
    # TODO: add more test cases
    return True if sampled == '1' else False


def parse_debug(headers):
    return True if headers.get(FLAGS_HEADER, '0') == '1' else False


def make_context(headers):
    # TODO: add validation for trace_id/span_id/parent_id

    # normalize header names just in case someone passed regular dict
    # instead dict with case insensitive keys
    headers = {k.lower(): v for k, v in headers.items()}

    if not all(h in headers for h in (
            TRACE_ID_HEADER.lower(), SPAN_ID_HEADER.lower())):
        return None

    context = TraceContext(
        trace_id=headers.get(TRACE_ID_HEADER.lower()),
        parent_id=headers.get(PARENT_ID_HEADER.lower(), None),
        span_id=headers.get(SPAN_ID_HEADER.lower()),
        sampled=parse_sampled(headers),
        shared=False,
        debug=parse_debug(headers),
    )
    return context
