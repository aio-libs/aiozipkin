import ipaddress

import aiohttp
from aiohttp.web import HTTPException

from .constants import HTTP_METHOD, HTTP_PATH, HTTP_STATUS_CODE
from .helpers import CLIENT, SERVER, make_context, parse_debug, parse_sampled


APP_AIOZIPKIN_KEY = 'aiozipkin_tracer'
REQUEST_AIOZIPKIN_KEY = 'aiozipkin_span'


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


def middleware_maker(tracer_key=APP_AIOZIPKIN_KEY,
                     request_key=REQUEST_AIOZIPKIN_KEY):
    async def middleware_factory(app, handler):
        async def aiozipkin_middleware(request):
            context = make_context(request.headers)
            tracer = app[tracer_key]

            if context is None:
                sampled = parse_sampled(request.headers)
                debug = parse_debug(request.headers)
                span = tracer.new_trace(sampled=sampled, debug=debug)
            else:
                span = tracer.join_span(context)

            request[request_key] = span

            if span.is_noop:
                resp = await handler(request)
                return resp

            with span:
                span_name = '{0} {1}'.format(request.method.upper(),
                                             request.path)
                span.name(span_name)
                span.kind(SERVER)
                span.tag(HTTP_PATH, request.path)
                span.tag(HTTP_METHOD, request.method.upper())
                _set_remote_endpoint(span, request)

                try:
                    resp = await handler(request)
                except HTTPException as e:
                    span.tag(HTTP_STATUS_CODE, e.status)
                    raise

                span.tag(HTTP_STATUS_CODE, resp.status)
            return resp

        return aiozipkin_middleware

    return middleware_factory


def setup(app, tracer,
          tracer_key=APP_AIOZIPKIN_KEY,
          request_key=REQUEST_AIOZIPKIN_KEY):
    app[tracer_key] = tracer
    app.middlewares.append(middleware_maker(tracer_key, request_key))

    # register cleanup signal to close zipkin connections
    async def close_aiozipkin(app):
        await app[tracer_key].close()

    app.on_cleanup.append(close_aiozipkin)

    return app


def get_tracer(app, tracer_key=APP_AIOZIPKIN_KEY):
    return app[tracer_key]


def request_span(request, request_key=REQUEST_AIOZIPKIN_KEY):
    return request[request_key]


class ZipkingClientSignals:

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
