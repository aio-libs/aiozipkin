API
===

Core API Reference
------------------

.. module:: aiozipkin
.. currentmodule:: aiozipkin


.. data:: CLIENT

    Constant indicates that span has been created on client side.

.. data:: SERVER

    Constant indicates that span has been created on server side.

.. data:: PRODUCER

    Constant indicates that span has been created by messsage producer.

.. data:: CONSUMER

    Constant indicates that span has been created by messsage consumer.

.. function:: make_context(headers: Dict[str, str])

    Creates tracing context object from from headers mapping if possible,
    otherwise returns `None`.

    :param dict headers: hostname to serve monitor telnet server
    :returns: TraceContext object or None

.. cofunction:: create(zipkin_address, local_endpoint, sample_rate, send_interval, loop, ignored_exceptions)

   Creates Tracer object

   :param Endpoint zipkin_address: information related to service address \
    and name, where current zipkin tracer is installed
   :param Endpoint local_endpoint: hostname to serve monitor telnet server
   :param float sample_rate: hostname to serve monitor telnet server
   :param float send_inteval: hostname to serve monitor telnet server
   :param asyncio.EventLoop loop: hostname to serve monitor telnet server
   :param Optional[List[Type[Exception]]]: ignored_exceptions list of exceptions \
    which will not be labeled as error
   :returns: Tracer

.. cofunction:: create_custom(transport, sampler, local_endpoint, ignored_exceptions)

    Creates Tracer object with a custom Transport and Sampler implementation.

    :param TransportABC transport: custom transport implementation
    :param SamplerABC sampler: custom sampler implementation
    :param Endpoint local_endpoint: hostname to serve monitor telnet server
    :param Optional[List[Type[Exception]]]: ignored_exceptions list of exceptions \
     which will not be labeled as error
    :returns: Tracer

.. class:: Endpoint(serviceName: str, ipv4=None, ipv6=None, port=None)

   This this simple data only class, just holder for service related
   information:

   .. attribute:: serviceName
   .. attribute:: ipv4
   .. attribute:: ipv6
   .. attribute:: port

.. class:: TraceContext(trace_id, parent_id, span_id, sampled, debug, shared)

   Immutable class with trace related data that travels across
   process boundaries.:

   :param str trace_id: hostname to serve monitor telnet server
   :param Optional[str] parent_id: hostname to serve monitor telnet server
   :param str span_id: hostname to serve monitor telnet server
   :param str sampled: hostname to serve monitor telnet server
   :param str debug: hostname to serve monitor telnet server
   :param float shared: hostname to serve monitor telnet server

   .. method:: make_headers()

     :rtype dict: hostname to serve monitor telnet server

.. class:: Sampler(trace_id, parent_id, span_id, sampled, debug, shared)

   TODO: add

   :param float sample_rate: XXX
   :param Optional[int] seed: seed value for random number generator

   .. method:: is_sampled(trace_id)

     XXX

     :rtype bool: hostname to serve monitor telnet server


Aiohttp integration API
-----------------------

API for integration with *aiohttp.web*, just calling `setup` is enough for
zipkin to start tracking requests. On high level attached plugin registers
middleware that starts span on beginning of request and closes it on finish,
saving important metadata, like route, status code etc.


.. data:: APP_AIOZIPKIN_KEY

    Key, for aiohttp application, where aiozipkin related data is saved. In case
    for some reason you want to use 2 aiozipkin instances or change default
    name, this parameter should not be used.

.. data:: REQUEST_AIOZIPKIN_KEY

    Key, for aiohttp request, where aiozipkin span related to current request is
    located.

.. function:: setup(app, tracer, tracer_key=APP_AIOZIPKIN_KEY, request_key=APP_AIOZIPKIN_KEY)

   Sets required parameters in aiohttp applications for aiozipkin.

   Tracer added into application context and cleaned after application
   shutdown. You can provide custom tracer_key, if default name is not
   suitable.

   :param aiottp.web.Application app: application for tracer to attach
   :param Tracer tracer: aiozipkin tracer
   :param List skip_routes: list of routes not to be traced
   :param str tracer_key: key for aiozipkin state in aiohttp Application
   :param str request_key: key for Span in request object
   :returns: aiottp.web.Application

.. function:: get_tracer(app, tracer_key=APP_AIOZIPKIN_KEY)

   Sets required parameters in aiohttp applications for aiozipkin.

   By default tracer has APP_AIOZIPKIN_KEY in aiohttp application context,
   you can provide own key, if for some reason default one is not suitable.

   :param aiottp.web.Application app: application for tracer to attach
   :param str tracer_key: key where tracerd stored in app

.. function:: request_span(request, request_key=REQUEST_AIOZIPKIN_KEY)

    Return span created by middleware from request context, you can use it
    as parent on next child span.

   :param aiottp.web.Request app: application for tracer to attach
   :param str request_key: key where stpan stored in request

.. function:: make_trace_config(tracer)

    Creates configuration compatible with aiohttp client. It attaches to
    reslevant hooks and annotates timing.

   :param Tracer tracer: to install in aiohttp tracer config
   :returns: aiohttp.TraceConfig
