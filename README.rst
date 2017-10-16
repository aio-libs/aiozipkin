aiozipkin
==========
.. image:: https://travis-ci.org/aio-libs/aiozipkin.svg?branch=master
    :target: https://travis-ci.org/aio-libs/aiozipkin
.. image:: https://codecov.io/gh/aio-libs/aiozipkin/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/aio-libs/aiozipkin
.. image:: https://img.shields.io/pypi/v/aiozipkin.svg
    :target: https://pypi.python.org/pypi/aiozipkin
.. image:: https://readthedocs.org/projects/aiozipkin/badge/?version=latest
    :target: http://aiozipkin.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://badges.gitter.im/Join%20Chat.svg
    :target: https://gitter.im/aio-libs/Lobby
    :alt: Chat on Gitter

**aiozipkin** is Python 3.5+ module that adds distributed tracing capabilities
from asyncio applications with Zipkin (http://zipkin.io) server instrumentation.

Zipkin is a distributed tracing system. It helps gather timing data needed
to troubleshoot latency problems in microservice architectures. It manages
both the collection and lookup of this data. Zipkin’s design is based on
the Google Dapper paper.


.. image:: https://raw.githubusercontent.com/aio-libs/aiozipkin/master/docs/zipkin_animation2.gif
    :alt: zipkin ui animation


Example
-------

.. code:: python

    import asyncio
    import aiozipkin as az


    async def run():
        # setup zipkin client
        zipkin_address = "http://127.0.0.1:9411"
        endpoint = az.create_endpoint(
            "simple_service", ipv4="127.0.0.1", port=8080)
        tracer = az.create(zipkin_address, endpoint)

        # create and setup new trace
        with tracer.new_trace(sampled=True) as span:
            span.name("root_span")
            span.tag("span_type", "root")
            span.kind(az.CLIENT)
            span.annotate("SELECT * FROM")
            # imitate long SQL query
            await asyncio.sleep(0.1)
            span.annotate("END SQL")

            # create child span
            with tracer.new_child(span.context) as nested_span:
                nested_span.name("nested_span_1")
                nested_span.kind(az.CLIENT)
                nested_span.tag("span_type", "inner1")
                nested_span.remote_endpoint("remote_service_1")
                await asyncio.sleep(0.01)

            # create other child span
            with tracer.new_child(span.context) as nested_span:
                nested_span.name("nested_span_2")
                nested_span.kind(az.CLIENT)
                nested_span.remote_endpoint("remote_service_2")
                nested_span.tag("span_type", "inner2")
                await asyncio.sleep(0.01)

            await asyncio.sleep(30)
            await tracer.close()

    if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run())


Installation
------------
Installation process is simple, just::

    $ pip install aiozipkin


Requirements
------------

* Python_ 3.5+
* aiohttp_


.. _PEP492: https://www.python.org/dev/peps/pep-0492/
.. _Python: https://www.python.org
.. _aiohttp: https://github.com/KeepSafe/aiohttp
.. _asyncio: http://docs.python.org/3.5/library/asyncio.html
.. _uvloop: https://github.com/MagicStack/uvloop
