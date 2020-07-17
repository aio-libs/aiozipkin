.. aiozipkin documentation master file, created by
   sphinx-quickstart on Sun Dec 11 17:08:38 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

aiozipkin's documentation!
===========================


**aiozipkin** is Python 3.6+ module that adds distributed tracing capabilities
for asyncio_ applications with zipkin (http://zipkin.io) server instrumentation.

zipkin_ is a distributed tracing system. It helps gather timing data needed
to troubleshoot latency problems in microservice architectures. It manages
both the collection and lookup of this data. Zipkin’s design is based on
the Google Dapper paper.

Applications instrumented with **aiozipkin** report timing data to zipkin_.
The Zipkin UI also presents a Dependency diagram showing how many traced
requests went through each application. If you are troubleshooting latency
problems or errors, you can filter or sort all traces based on the
application, length of trace, annotation, or timestamp.


.. image:: https://raw.githubusercontent.com/aio-libs/aiozipkin/master/docs/zipkin_animation2.gif
    :alt: zipkin ui animation


Features
--------
* Distributed tracing capabilities to **asyncio** applications.
* Supports zipkin_ ``v2`` protocol.
* Easy to use API.
* Explicit context handling, no thread local variables.
* Can work with jaeger_ and stackdriver_ (google_) through zipkin compatible API.
* Can be integrated with AWS X-Ray by aws_ proxy.

Contents
--------

.. toctree::
   :maxdepth: 2

   tutorial
   examples
   other
   api
   contributing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _PEP492: https://www.python.org/dev/peps/pep-0492/
.. _Python: https://www.python.org
.. _aiohttp: https://github.com/aio-libs/aiohttp
.. _asyncio: http://docs.python.org/3/library/asyncio.html
.. _uvloop: https://github.com/MagicStack/uvloop
.. _zipkin: http://zipkin.io
.. _jaeger: http://jaeger.readthedocs.io/en/latest/
.. _stackdriver: https://cloud.google.com/stackdriver/
.. _google: https://cloud.google.com/trace/docs/zipkin
.. _aws: https://github.com/openzipkin/zipkin-aws
