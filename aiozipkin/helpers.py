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
