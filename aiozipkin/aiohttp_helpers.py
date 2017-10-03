from .helpers import make_context, SERVER


APP_AIOZIPKIN_KEY = "aiozipkin_tracer"
REQUEST_AIOZIPKIN_KEY = "aiozipkin_span"


def middleware_maker(tracer_key=APP_AIOZIPKIN_KEY,
                     request_key=REQUEST_AIOZIPKIN_KEY):
    async def middleware_factory(app, handler):
        async def aiozipkin_middleware(request):
            context = make_context(request.headers)
            tracer = app[tracer_key]
            with tracer.join_or_create(context) as span:
                span_name = '{0} {1}'.format(request.method, request.path)
                span.kind(SERVER)
                span.name(span_name)
                span.tag('path', request.path)
                request[request_key] = span

                resp = await handler(request)

                span.tag('status_code', resp.status)
                return resp

        return aiozipkin_middleware
    return middleware_factory


def setup(app, tracer,
          tracer_key=APP_AIOZIPKIN_KEY,
          request_key=REQUEST_AIOZIPKIN_KEY):
    app[tracer_key] = tracer
    app.middlewares.append(middleware_maker(tracer_key, request_key))
    return app


def get_tracer(app, tracer_key=APP_AIOZIPKIN_KEY):
    return app[tracer_key]


def request_span(request, request_key=REQUEST_AIOZIPKIN_KEY):
    return request[request_key]
