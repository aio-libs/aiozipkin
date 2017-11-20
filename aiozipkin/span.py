from .constants import ERROR
from .helpers import Endpoint, make_timestamp


class NoopSpan:
    def __init__(self, tracer, context):
        self._context = context
        self._tracer = tracer

    @property
    def is_noop(self):
        return True

    @property
    def context(self):
        return self._context

    @property
    def tracer(self):
        return self._tracer

    def start(self, ts=None):
        return self

    def finish(self, ts=None):
        return self

    def remote_endpoint(self, servce_name, *, ipv4=None, ipv6=None, port=None):
        return self

    def tag(self, key, value):
        return self

    def annotate(self, value, ts=None):
        return self

    def kind(self, span_kind):
        return self

    def name(self, span_name):
        return self

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.finish()


class Span(NoopSpan):
    def __init__(self, tracer, context, record):
        super().__init__(tracer, context)
        self._record = record

    @property
    def is_noop(self):
        return False

    @property
    def context(self):
        return self._context

    @property
    def tracer(self):
        return self._tracer

    def start(self, ts=None):
        ts = make_timestamp(ts)
        self._record.start(ts)
        return self

    def finish(self, ts=None, exception=None):
        if exception is not None:
            self.tag(ERROR, str(exception))
        ts = make_timestamp(ts)
        self._record.finish(ts)
        self._tracer._send(self._record)
        return self

    def remote_endpoint(self, servce_name, *, ipv4=None, ipv6=None, port=None):
        endpoint = Endpoint(servce_name, ipv4, ipv6, port)
        self._record.remote_endpoint(endpoint)
        return self

    def tag(self, key, value):
        self._record.set_tag(key, value)
        return self

    def annotate(self, value, ts=None):
        ts = make_timestamp(ts)
        self._record.annotate(value, ts)
        return self

    def kind(self, span_kind):
        self._record.kind(span_kind)
        return self

    def name(self, span_name):
        self._record.name(span_name)
        return self

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.finish(exception=exception_value)
