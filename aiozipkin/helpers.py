import time
from typing import NamedTuple, Optional, Dict, List, Any

from .mypy_types import Headers, OptBool, OptInt, OptStr, OptTs


# possible span kinds
CLIENT = 'CLIENT'
SERVER = 'SERVER'
PRODUCER = 'PRODUCER'
CONSUMER = 'CONSUMER'

# zipkin headers, for more information see:
# https://github.com/openzipkin/b3-propagation

TRACE_ID_HEADER = 'X-B3-TraceId'
SPAN_ID_HEADER = 'X-B3-SpanId'
PARENT_ID_HEADER = 'X-B3-ParentSpanId'
FLAGS_HEADER = 'X-B3-Flags'
SAMPLED_ID_HEADER = 'X-B3-Sampled'


_TraceContext = NamedTuple(
    'TraceContext', [
        ('trace_id', str),
        ('parent_id', OptStr),
        ('span_id', str),
        ('sampled', bool),
        ('debug', bool),
        ('shared', bool),
        ]
)


class TraceContext(_TraceContext):
    """Immutable class with trace related data that travels across
    process boundaries.
    """

    def make_headers(self) -> Headers:
        """Creates dict with zipkin headers from available context.

        Resulting dict should be passed to HTTP client  propagate contest
        to other services.
        """
        return make_headers(self)


Endpoint = NamedTuple(
    'Endpoint', [('serviceName', str),
                 ('ipv4', OptStr),
                 ('ipv6', OptStr),
                 ('port', OptInt)]
)


def create_endpoint(servce_name: str, *,
                    ipv4: OptStr=None,
                    ipv6: OptStr=None,
                    port: OptInt=None):
    """Factory function to create Endpoint object.
    """
    return Endpoint(servce_name, ipv4, ipv6, port)


def make_timestamp(ts: OptTs=None) -> int:
    """Create zipkin timestamp in microseconds, or convert available one
    from second. Useful when user supply ts from time.time() call.
    """
    ts = ts if ts is not None else time.time()
    return int(ts * 1000 * 1000)  # microseconds


def make_headers(context: TraceContext) -> Headers:
    """Creates dict with zipkin headers from supplied trace context.
    """
    headers = {
        TRACE_ID_HEADER: context.trace_id,
        SPAN_ID_HEADER: context.span_id,
        FLAGS_HEADER: '0',
        SAMPLED_ID_HEADER: '1' if context.sampled else '0',
    }
    if context.parent_id is not None:
        headers[PARENT_ID_HEADER] = context.parent_id
    return headers


def parse_sampled(headers: Headers) -> OptBool:
    sampled = headers.get(SAMPLED_ID_HEADER.lower(), None)
    if sampled is None or sampled == '':
        return None
    # TODO: add more test cases
    return True if sampled == '1' else False


def parse_debug(headers: Headers) -> bool:
    return True if headers.get(FLAGS_HEADER, '0') == '1' else False


def make_context(headers: Headers) -> Optional[TraceContext]:
    """Converts available headers to TraceContext, if headers mapping does
    not contain zipkin headers, function returns None.
    """
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


OptKeys = Optional[List[str]]


def filter_none(data: Dict[str, Any],
                keys: OptKeys=None) -> Dict[str, Any]:
    """Filter keys from dict with None values.

    Check occurs only on root level. If list of keys specified, filter
    works only for selected keys
    """

    def limited_filter(k: str, v: Any) -> bool:
        return k not in keys or v is not None  # type: ignore

    def full_filter(k: str, v: Any) -> bool:
        return v is not None

    f = limited_filter if keys is not None else full_filter
    return {k: v for k, v in data.items() if f(k, v)}
