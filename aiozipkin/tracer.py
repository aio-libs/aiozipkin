from .helpers import TraceContext
from .record import Record
from .sampler import Sampler
from .span import Span, NoopSpan
from .transport import Transport
from .utils import generate_random_64bit_string, generate_random_128bit_string


def create(zipkin_address, local_endpoint):
    sampler = Sampler()
    transport = Transport(zipkin_address)
    return Tracer(transport, sampler, local_endpoint)


class Tracer:
    def __init__(self, transport, sampler, local_endpoint):
        self._records = {}
        self._transport = transport
        self._sampler = sampler
        self._local_endpoint = local_endpoint

    def new_trace(self):
        context = self._next_context(None, None)
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
            return NoopSpan(new_context)
        return self.to_span(new_context)

    def join_or_create(self, context=None):
        if context is not None:
            return self.join_span(context)
        new_context = self._next_context(context)
        return self.to_span(new_context)

    def child_or_create(self, context=None):
        if context is None:
            return self.new_trace()
        return self.new_child(context)

    def to_span(self, context):
        if not context.sampled:
            return NoopSpan(context)

        record = Record(context, self._local_endpoint)
        self._records[context] = record
        return Span(self, context, record)

    def _send(self, record):
        self._records.pop(record._context, None)
        self._transport.send(record)

    def _next_context(self, context=None, sampled=None):
        span_id = generate_random_64bit_string()
        if context is not None:
            new_context = context._replace(
                span_id=span_id, parent_id=context.span_id, shared=False)
            return new_context
        trace_id = generate_random_128bit_string()

        if sampled is None:
            sampled = self._sampler.is_sampled(trace_id)

        new_context = TraceContext(
            trace_id=trace_id,
            parent_id=None,
            span_id=span_id,
            sampled=sampled,
            debug=False,
            shared=False)
        return new_context

    async def close(self):
        await self._transport.close()
