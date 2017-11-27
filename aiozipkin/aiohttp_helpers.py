import ipaddress
from aiohttp.web import HTTPException

from .constants import HTTP_PATH, HTTP_STATUS_CODE, HTTP_METHOD
from .helpers import make_context, SERVER, parse_debug, parse_sampled

APP_AIOZIPKIN_KEY = 'aiozipkin_tracer'
REQUEST_AIOZIPKIN_KEY = 'aiozipkin_span'


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
