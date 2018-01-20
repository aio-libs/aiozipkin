import ipaddress

import aiohttp
from aiohttp.web import HTTPException

from .constants import HTTP_METHOD, HTTP_PATH, HTTP_STATUS_CODE
from .helpers import CLIENT, SERVER, make_context, parse_debug, parse_sampled


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


def _set_remote_endpoint(span, request):
    peername = request.remote
    if peername is not None:
        kwargs = {}
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


def _get_span(request, tracer):
    # builds span from incoming request, if no context found, create
    # new span
    context = make_context(request.headers)

    if context is None:
        sampled = parse_sampled(request.headers)
        debug = parse_debug(request.headers)
        span = tracer.new_trace(sampled=sampled, debug=debug)
    else:
        span = tracer.join_span(context)
    return span


def _set_span_properties(span, request):
    span_name = '{0} {1}'.format(request.method.upper(),
                                 request.path)
    span.name(span_name)
    span.kind(SERVER)
    span.tag(HTTP_PATH, request.path)
    span.tag(HTTP_METHOD, request.method.upper())
    _set_remote_endpoint(span, request)


# TODO: new aiohttp 3.0.0 has a bit different API for middlewares
# should be reworked once 3.0.0 out, do we care about backward compatibility
def middleware_maker(skip_routes=None, tracer_key=APP_AIOZIPKIN_KEY,
                     request_key=REQUEST_AIOZIPKIN_KEY):

    skip_routes_set = set(skip_routes) if skip_routes else set()

    async def middleware_factory(app, handler):
        async def aiozipkin_middleware(request):
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

    return middleware_factory


def setup(app, tracer, *,
          skip_routes=None,
          tracer_key=APP_AIOZIPKIN_KEY,
          request_key=REQUEST_AIOZIPKIN_KEY):
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
    async def close_aiozipkin(app):
        await app[tracer_key].close()

    app.on_cleanup.append(close_aiozipkin)

    return app


def get_tracer(app, tracer_key=APP_AIOZIPKIN_KEY):
    """Returns tracer object from application context.

    By default tracer has APP_AIOZIPKIN_KEY in aiohttp application context,
    you can provide own key, if for some reason default one is not suitable.
    """
    return app[tracer_key]


def request_span(request, request_key=REQUEST_AIOZIPKIN_KEY):
    """Return span created by middleware from request context, you can use it
    as parent on next child span.
    """
    return request[request_key]


class ZipkingClientSignals:
    """Class contains signal handler for aiohttp client. Handlers executed
    only if aiohttp session contains tracer context with span.
    """

    def __init__(self, tracer):
        self._tracer = tracer

    def _has_span(self, trace_config_ctx):
        trace_request_ctx = trace_config_ctx.trace_request_ctx
        has_span = (isinstance(trace_request_ctx, dict) and
                    'span_context' in trace_request_ctx)
        return has_span

    async def on_request_start(self, session, trace_config_ctx, method, url,
                               headers):
        if not self._has_span(trace_config_ctx):
            return

        span_context = trace_config_ctx.trace_request_ctx['span_context']
        span = self._tracer.new_child(span_context)
        trace_config_ctx._span = span
        span.start()
        span_name = 'client {0} {1}'.format(method.upper(), url.path)
        span.name(span_name)
        span.kind(CLIENT)

        propagate_headers = (trace_config_ctx
                             .trace_request_ctx
                             .get('propagate_headers', True))
        if propagate_headers:
            span_headers = span.context.make_headers()
            headers.update(span_headers)

    async def on_request_end(self, session, trace_config_ctx, method, url,
                             headers, resp):
        if not self._has_span(trace_config_ctx):
            return

        span = trace_config_ctx._span
        span.finish()
        delattr(trace_config_ctx, '_span')

    async def on_request_exception(self, session, trace_config_ctx, method,
                                   url, headers, error):
        if not self._has_span(trace_config_ctx):
            return
        span = trace_config_ctx._span
        span.finish(exception=error)
        delattr(trace_config_ctx, '_span')


def make_trace_config(tracer):
    trace_config = aiohttp.TraceConfig()
    zipkin = ZipkingClientSignals(tracer)

    trace_config.on_request_start.append(zipkin.on_request_start)
    trace_config.on_request_end.append(zipkin.on_request_end)
    trace_config.on_request_exception.append(zipkin.on_request_exception)
    return trace_config
