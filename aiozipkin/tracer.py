from typing import Optional, Dict  # flake8: noqa

from .helpers import TraceContext, Endpoint
from .mypy_types import OptLoop, OptBool
from .record import Record
from .sampler import Sampler
from .span import Span, NoopSpan, SpanAbc
from .transport import Transport
from .utils import generate_random_64bit_string, generate_random_128bit_string


class Tracer:
    def __init__(self,
                 transport: Transport,
                 sampler: Sampler,
                 local_endpoint: Endpoint) -> None:
        self._records = {}  # type: Dict[TraceContext, Record]
        self._transport = transport
        self._sampler = sampler
        self._local_endpoint = local_endpoint

    def new_trace(self,
                  sampled: OptBool=None,
                  debug: bool=False) -> SpanAbc:
        context = self._next_context(None, sampled=sampled, debug=debug)
        return self.to_span(context)

    def join_span(self, context: TraceContext) -> SpanAbc:
        new_context = context
        if context.sampled is None:
            sampled = self._sampler.is_sampled(context.trace_id)
            new_context = new_context._replace(sampled=sampled)
        else:
            new_context = new_context._replace(shared=True)
        return self.to_span(new_context)

    def new_child(self, context: TraceContext) -> SpanAbc:
        new_context = self._next_context(context)
        if not context.sampled:
            return NoopSpan(self, new_context)
        return self.to_span(new_context)

    def to_span(self, context: TraceContext) -> SpanAbc:
        if not context.sampled:
            return NoopSpan(self, context)

        record = Record(context, self._local_endpoint)
        self._records[context] = record
        return Span(self, context, record)

    def _send(self, record: Record) -> None:
        self._records.pop(record._context, None)
        self._transport.send(record)

    def _next_context(self,
                      context: Optional[TraceContext]=None,
                      sampled: OptBool=None,
                      debug: bool=False) ->TraceContext:
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

    async def close(self) -> None:
        await self._transport.close()


def create(zipkin_address: str,
           local_endpoint: Endpoint, *,
           sample_rate: float=0.01,
           send_inteval: float=5,
           loop: OptLoop=None) -> Tracer:
    sampler = Sampler(sample_rate=sample_rate)
    transport = Transport(zipkin_address, send_inteval=send_inteval, loop=loop)
    return Tracer(transport, sampler, local_endpoint)
