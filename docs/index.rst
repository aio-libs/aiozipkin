.. aiozipkin documentation master file, created by
   sphinx-quickstart on Sun Dec 11 17:08:38 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

aiozipkin's documentation!
===========================

**aiozipkin** is Python 3.5+ module that adds distributed tracing capabilities
from asyncio applications with Zipkin (http://zipkin.io) server instrumentation.

Zipkin is a distributed tracing system. It helps gather timing data needed
to troubleshoot latency problems in microservice architectures. It manages
both the collection and lookup of this data. Zipkin’s design is based on
the Google Dapper paper.


.. image:: https://raw.githubusercontent.com/aio-libs/aiozipkin/master/docs/zipkin_animation2.gif
    :alt: zipkin ui animation


Features
--------
 * Telnet server that provides insides of operation of you app

 * Supported several commands that helps to list, cancel and trace runnin
   asyncio_ tasks

 * Provided python REPL capabilities, that executed in running event loop,
   helps to inspect state of your ``asyncio`` application

Contents
--------

.. toctree::
   :maxdepth: 2

   tutorial
   examples
   api
   contributing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _PEP492: https://www.python.org/dev/peps/pep-0492/
.. _Python: https://www.python.org
.. _aioconsole: https://github.com/vxgmichel/aioconsole
.. _aiohttp: https://github.com/KeepSafe/aiohttp
.. _asyncio: http://docs.python.org/3.5/library/asyncio.html
.. _curio: https://github.com/dabeaz/curio
.. _uvloop: https://github.com/MagicStack/uvloop
