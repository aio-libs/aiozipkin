API
===

Core API Refernece
------------------

.. module:: aiozipkin
.. currentmodule:: aiozipkin


.. data:: CLIENT

    Contant indicates that span created on client side.

.. data:: SERVER

    Contant indicates that span created on server side.

.. data:: PRODUCER

    Contant indicates that span created by messsage producer.

.. data:: CONSUMER

    Contant indicates that span created by messsage consumer.

.. function:: make_context(headers: Dict[str, str])

    Creates tracing context object from from headers mapping if possible,
    otherwise retursns `None`.

    :param dict headers: hostname to serve monitor telnet server
    :returns: TraceContext object or None

.. cofunction:: create(zipkin_address, local_endpoint, sample_rate, send_inteval, loop)

   Creates Tracer object

   :param Endpoint zipkin_address: information related to service anddress \
    and name, where current zipkin tracer installed
   :param Endpoint local_endpoint: hostname to serve monitor telnet server
   :param float sample_rate: hostname to serve monitor telnet server
   :param float send_inteval: hostname to serve monitor telnet server
   :param asyncio.EventLoop loop: hostname to serve monitor telnet server
   :returns: Tracer

.. class:: Endpoint(serviceName: str, ipv4=None, ipv6=None, port=None)

   This this simple data only class, just holder for the servcie related
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


Aiohtp integration API
----------------------

.. data:: APP_AIOZIPKIN_KEY

    Key, for aiohttp application, where aiozipkin data saved.

.. data:: REQUEST_AIOZIPKIN_KEY

    Key, for aiohttp request, where aiozipkin span sits

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
