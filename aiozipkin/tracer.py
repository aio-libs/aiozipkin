from .helpers import TraceContext
from .record import Record
from .sampler import Sampler
from .span import Span, NoopSpan
from .transport import Transport
from .utils import generate_random_64bit_string, generate_random_128bit_string


def create(zipkin_address, local_endpoint, *, sample_rate=0.01, send_inteval=5,
           loop=None):
    sampler = Sampler(sample_rate=sample_rate)
    transport = Transport(zipkin_address, send_inteval=send_inteval, loop=loop)
    return Tracer(transport, sampler, local_endpoint)


class Tracer:
    def __init__(self, transport, sampler, local_endpoint):
        self._records = {}
        self._transport = transport
        self._sampler = sampler
        self._local_endpoint = local_endpoint

    def new_trace(self, sampled=None, debug=False):
        context = self._next_context(None, sampled=sampled, debug=debug)
        return self.to_span(context)

    def join_span(self, context):
        new_context = context
        if context.sampled is None:
            sampled = self._sampler.is_sampled(context.trace_id)
            new_context = new_context._replace(sampled=sampled)
        else:
            new_context = new_context._replace(shared=True)
        return self.to_span(new_context)

    def new_child(self, context):
        new_context = self._next_context(context)
        if not context.sampled:
            return NoopSpan(self, new_context)
        return self.to_span(new_context)

    def to_span(self, context):
        if not context.sampled:
            return NoopSpan(self, context)

        record = Record(context, self._local_endpoint)
        self._records[context] = record
        return Span(self, context, record)

    def _send(self, record):
        self._records.pop(record._context, None)
        self._transport.send(record)

    def _next_context(self, context=None, sampled=None, debug=False):
        span_id = generate_random_64bit_string()
        if context is not None:
            new_context = context._replace(
                span_id=span_id,
                parent_id=context.span_id,
                shared=False)
            return new_context

        trace_id = generate_random_128bit_string()
        if sampled is None:
            sampled = self._sampler.is_sampled(trace_id)

        new_context = TraceContext(
            trace_id=trace_id,
            parent_id=None,
            span_id=span_id,
            sampled=sampled,
            debug=debug,
            shared=False)
        return new_context

    async def close(self):
        await self._transport.close()
