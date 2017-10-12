Microservices Demo
==================

Example of microservices project using aiohttp_. There are 5 services, which
calls each other to serve request. You can explore traces and services
interconnection in Zipkin UI.


Installation
============

Clone repository and install library::

    $ git clone git@github.com:aio-libs/aiozipkin.git
    $ cd aiozipkin
    $ pip install -e .
    $ pip install -r requirements-dev.txt

Create start zipkin server, make sure you have docker installed::

    make zipkin_start

To stop zipkin server (stop and remove docker container)::

    make zipkin_stop

Open browser::

    http://127.0.0.1:9001


Click link on rendered page, as result first service will start chain of
http calls to other services. You can investigate that chain and timing
in Zipkin UI.

Zipkin UI available::

    http://127.0.0.1:9411/zipkin/



Requirements
============
* aiohttp_

.. _Python: https://www.python.org
.. _aiohttp: https://github.com/KeepSafe/aiohttp
