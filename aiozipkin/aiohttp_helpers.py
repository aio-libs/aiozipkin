import sys
import ipaddress
from types import SimpleNamespace
from typing import cast, Optional, Dict, Any, Set, Awaitable, Callable, Generator  # noqa
from contextlib import contextmanager

import aiohttp
from aiohttp.web import (HTTPException, Request, Application, Response,
                         middleware)
from aiohttp.web_urldispatcher import AbstractRoute
from aiohttp.tracing import (TraceRequestStartParams, TraceRequestEndParams,
                             TraceRequestExceptionParams)

from .constants import HTTP_METHOD, HTTP_PATH, HTTP_STATUS_CODE, HTTP_ROUTE
from .helpers import (CLIENT, SERVER, make_context, parse_debug_header,
                      parse_sampled_header, TraceContext)
from .span import SpanAbc
from .tracer import Tracer


APP_AIOZIPKIN_KEY = 'aiozipkin_tracer'
REQUEST_AIOZIPKIN_KEY = 'aiozipkin_span'


__all__ = (
    'setup',
    'get_tracer',
    'request_span',
    'middleware_maker',
    'make_trace_config',
    'APP_AIOZIPKIN_KEY',
    'REQUEST_AIOZIPKIN_KEY',
)

Handler = Callable[[Request], Awaitable[Response]]
Middleware = Callable[[Application, Handler], Awaitable[Handler]]


def _set_remote_endpoint(span: SpanAbc, request: Request) -> None:
    peername = request.remote
    if peername is not None:
        kwargs: Dict[str, Any] = {}
        try:
            peer_ipaddress = ipaddress.ip_address(peername)
        except ValueError:
            pass
        else:
            if isinstance(peer_ipaddress, ipaddress.IPv4Address):
                kwargs['ipv4'] = str(peer_ipaddress)
            else:
                kwargs['ipv6'] = str(peer_ipaddress)
        if kwargs:
            span.remote_endpoint(None, **kwargs)


def _get_span(request: Request, tracer: Tracer) -> SpanAbc:
    # builds span from incoming request, if no context found, create
    # new span
    context = make_context(request.headers)

    if context is None:
        sampled = parse_sampled_header(request.headers)
        debug = parse_debug_header(request.headers)
        span = tracer.new_trace(sampled=sampled, debug=debug)
    else:
        span = tracer.join_span(context)
    return span


def _set_span_properties(span: SpanAbc, request: Request) -> None:
    span_name = '{0} {1}'.format(request.method.upper(),
                                 request.path)
    span.name(span_name)
    span.kind(SERVER)
    span.tag(HTTP_PATH, request.path)
    span.tag(HTTP_METHOD, request.method.upper())

    resource = request.match_info.route.resource
    # available only in aiohttp >= 3.3.1
    if getattr(resource, 'canonical', None) is not None:
        route = request.match_info.route.resource.canonical
        span.tag(HTTP_ROUTE, route)

    _set_remote_endpoint(span, request)


PY37 = sys.version_info >= (3, 7)

if PY37:
    from contextvars import ContextVar
    OptTraceVar = ContextVar[Optional[TraceContext]]
    zipkin_context: OptTraceVar = ContextVar(
        'zipkin_context', default=None)

    @contextmanager
    def set_context_value(
            context_var: OptTraceVar,
            value: TraceContext
    ) -> Generator[OptTraceVar, None, None]:
        token = context_var.set(value)
        try:
            yield context_var
        finally:
            context_var.reset(token)


def middleware_maker(skip_routes: Optional[AbstractRoute] = None,
                     tracer_key: str = APP_AIOZIPKIN_KEY,
                     request_key: str = REQUEST_AIOZIPKIN_KEY) -> Middleware:
    s = skip_routes
    skip_routes_set: Set[AbstractRoute] = set(s) if s else set()

    _middleware: Callable[[Middleware], Middleware] = middleware

    @_middleware
    async def aiozipkin_middleware(
            request: Request, handler: Handler) -> Response:
        # route is in skip list, we do not track anything with zipkin
        if request.match_info.route in skip_routes_set:
            resp = await handler(request)
            return resp

        tracer = request.app[tracer_key]
        span = _get_span(request, tracer)
        request[request_key] = span
        if span.is_noop:
            resp = await handler(request)
            return resp

        if PY37:
            with set_context_value(zipkin_context, span.context):
                with span:
                    _set_span_properties(span, request)
                    try:
                        resp = await handler(request)
                    except HTTPException as e:
                        span.tag(HTTP_STATUS_CODE, e.status)
                        raise
                    span.tag(HTTP_STATUS_CODE, resp.status)
        else:
            with span:
                _set_span_properties(span, request)
                try:
                    resp = await handler(request)
                except HTTPException as e:
                    span.tag(HTTP_STATUS_CODE, e.status)
                    raise
                span.tag(HTTP_STATUS_CODE, resp.status)

        return resp

    return aiozipkin_middleware


def setup(app: Application,
          tracer: Tracer, *,
          skip_routes: Optional[AbstractRoute] = None,
          tracer_key: str = APP_AIOZIPKIN_KEY,
          request_key: str = REQUEST_AIOZIPKIN_KEY) -> Application:
    """Sets required parameters in aiohttp applications for aiozipkin.

    Tracer added into application context and cleaned after application
    shutdown. You can provide custom tracer_key, if default name is not
    suitable.
    """
    app[tracer_key] = tracer
    m = middleware_maker(skip_routes=skip_routes,
                         tracer_key=tracer_key,
                         request_key=request_key)
    app.middlewares.append(m)

    # register cleanup signal to close zipkin transport connections
    async def close_aiozipkin(app: Application) -> None:
        await app[tracer_key].close()

    app.on_cleanup.append(close_aiozipkin)

    return app


def get_tracer(
        app: Application, tracer_key: str = APP_AIOZIPKIN_KEY) -> Tracer:
    """Returns tracer object from application context.

    By default tracer has APP_AIOZIPKIN_KEY in aiohttp application context,
    you can provide own key, if for some reason default one is not suitable.
    """
    return cast(Tracer, app[tracer_key])


def request_span(request: Request,
                 request_key: str = REQUEST_AIOZIPKIN_KEY) -> SpanAbc:
    """Returns span created by middleware from request context, you can use it
    as parent on next child span.
    """
    return cast(SpanAbc, request[request_key])


class ZipkinClientSignals:
    """Class contains signal handler for aiohttp client. Handlers executed
    only if aiohttp session contains tracer context with span.
    """

    def __init__(self, tracer: Tracer) -> None:
        self._tracer = tracer

    def _get_span_context(
            self, trace_config_ctx: SimpleNamespace) -> Optional[TraceContext]:
        trace_request_ctx = trace_config_ctx.trace_request_ctx
        has_explicit_context = (isinstance(trace_request_ctx, dict) and
                                'span_context' in trace_request_ctx)
        if has_explicit_context:
            r: TraceContext = trace_request_ctx['span_context']
            return r

        if PY37:
            has_implicit_context = zipkin_context.get() is not None
            if has_implicit_context:
                return zipkin_context.get()

        return None

    async def on_request_start(
        self,
        session: aiohttp.ClientSession,
        context: SimpleNamespace,
        params: TraceRequestStartParams
    ) -> None:
        span_context = self._get_span_context(context)
        if span_context is None:
            return

        p = params
        span = self._tracer.new_child(span_context)
        context._span = span
        span.start()
        span_name = 'client {0} {1}'.format(p.method.upper(), p.url.path)
        span.name(span_name)
        span.kind(CLIENT)

        ctx = context.trace_request_ctx
        propagate_headers = (ctx is None or
                             ctx.get('propagate_headers', True))
        if propagate_headers:
            span_headers = span.context.make_headers()
            p.headers.update(span_headers)

    async def on_request_end(
        self,
        session: aiohttp.ClientSession,
        context: SimpleNamespace,
        params: TraceRequestEndParams
    ) -> None:
        span_context = self._get_span_context(context)
        if span_context is None:
            return

        span = context._span
        span.finish()
        delattr(context, '_span')

    async def on_request_exception(
        self,
        session: aiohttp.ClientSession,
        context: SimpleNamespace,
        params: TraceRequestExceptionParams
    ) -> None:

        span_context = self._get_span_context(context)
        if span_context is None:
            return
        span = context._span
        span.finish(exception=params.exception)
        delattr(context, '_span')


def make_trace_config(tracer: Tracer) -> aiohttp.TraceConfig:
    """Creates aiohttp.TraceConfig with enabled aiozipking instrumentation
    for aiohttp client.
    """
    trace_config = aiohttp.TraceConfig()
    zipkin = ZipkinClientSignals(tracer)

    trace_config.on_request_start.append(zipkin.on_request_start)
    trace_config.on_request_end.append(zipkin.on_request_end)
    trace_config.on_request_exception.append(zipkin.on_request_exception)
    return trace_config
