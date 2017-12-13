from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, TypeVar, Optional

from .constants import ERROR
from .helpers import Endpoint, make_timestamp, TraceContext
from .mypy_types import OptInt, OptStr, OptTs
from .record import Record


if TYPE_CHECKING:
    from .tracer import Tracer  # flake8: noqa


T = TypeVar('T', bound='SpanAbc')


class SpanAbc(metaclass=ABCMeta):

    @property
    @abstractmethod
    def is_noop(self: T) -> bool:
        return True  # pragma: no cover

    @property
    @abstractmethod
    def context(self: T) -> TraceContext:
        pass  # pragma: no cover

    @property
    @abstractmethod
    def tracer(self: T) -> 'Tracer':
        pass  # pragma: no cover

    @abstractmethod
    def start(self: T, ts: OptTs=None) -> T:
        pass  # pragma: no cover

    @abstractmethod
    def finish(self: T, ts: OptTs=None,
               exception: Optional[Exception]=None) -> T:
        pass  # pragma: no cover

    @abstractmethod
    def remote_endpoint(self: T,
                        servce_name: str, *,
                        ipv4: OptStr=None,
                        ipv6: OptStr=None,
                        port: OptInt=None) -> T:
        pass  # pragma: no cover

    @abstractmethod
    def tag(self: T, key: str, value: str) -> T:
        pass  # pragma: no cover

    @abstractmethod
    def annotate(self: T,
                 value: str,
                 ts: OptTs=None) -> T:
        pass  # pragma: no cover

    @abstractmethod
    def kind(self: T, span_kind: str) -> T:
        pass  # pragma: no cover

    @abstractmethod
    def name(self: T, span_name: str) -> T:
        pass  # pragma: no cover

    def __enter__(self: T) -> T:
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        self.finish(exception=exception_value)


class NoopSpan(SpanAbc):
    def __init__(self, tracer: 'Tracer', context: TraceContext) -> None:
        self._context = context
        self._tracer = tracer

    @property
    def is_noop(self) -> bool:
        return True

    @property
    def context(self) -> TraceContext:
        return self._context

    @property
    def tracer(self) -> 'Tracer':
        return self._tracer

    def start(self, ts: OptTs=None) -> 'NoopSpan':
        return self

    def finish(self, ts: OptTs=None,
               exception: Optional[Exception]=None) -> 'NoopSpan':
        return self

    def remote_endpoint(self,
                        servce_name: str, *,
                        ipv4: OptStr=None,
                        ipv6: OptStr=None,
                        port: OptInt=None) -> 'NoopSpan':
        return self

    def tag(self, key: str, value: str) -> 'NoopSpan':
        return self

    def annotate(self, value: str, ts: OptTs=None) -> 'NoopSpan':
        return self

    def kind(self, span_kind: str) -> 'NoopSpan':
        return self

    def name(self, span_name: str) -> 'NoopSpan':
        return self


class Span(SpanAbc):
    def __init__(self, tracer: 'Tracer',
                 context: TraceContext,
                 record: Record) -> None:
        self._context = context
        self._tracer = tracer
        self._record = record

    @property
    def is_noop(self) -> bool:
        return False

    @property
    def context(self) -> TraceContext:
        return self._context

    @property
    def tracer(self) -> 'Tracer':
        return self._tracer

    def start(self, ts=None) -> 'Span':
        ts = make_timestamp(ts)
        self._record.start(ts)
        return self

    def finish(self, ts: OptTs=None,
               exception: Optional[Exception]=None) -> 'Span':
        if exception is not None:
            self.tag(ERROR, str(exception))
        ts = make_timestamp(ts)
        self._record.finish(ts)
        self._tracer._send(self._record)
        return self

    def remote_endpoint(self,
                        servce_name: str, *,
                        ipv4: OptStr=None,
                        ipv6: OptStr=None,
                        port: OptInt=None) -> 'Span':
        endpoint = Endpoint(servce_name, ipv4, ipv6, port)
        self._record.remote_endpoint(endpoint)
        return self

    def tag(self, key: str, value: str) -> 'Span':
        self._record.set_tag(key, value)
        return self

    def annotate(self, value: str, ts: OptTs=None) -> 'Span':
        ts = make_timestamp(ts)
        self._record.annotate(value, ts)
        return self

    def kind(self, span_kind: str) -> 'Span':
        self._record.kind(span_kind)
        return self

    def name(self, span_name: str) -> 'Span':
        self._record.name(span_name)
        return self
