Examples of aiozipkin usage
===========================

Below is a list of examples from `aiozipkin/examples
<https://github.com/aio-libs/aiozipkin/tree/master/examples>`_

Every example is a correct tiny python program.

.. _aiozipkin-examples-simple:

Basic Usage
-----------


.. literalinclude:: ../examples/simple.py

aiohttp Example
---------------

Full featured example with aiohttp application:

.. literalinclude:: ../examples/aiohttp_example.py


Fastapi
-------

Fastapi support can be found with the `starlette-zipkin
<https://pypi.org/project/starlette-zipkin/>`_ package.


Microservices Demo
------------------
There is a larger micro services example, using aiohttp. This demo consists of
five simple services that call each other, as result you can study client
server communication and zipkin integration for large projects. For more
information see:

`<https://github.com/aio-libs/aiozipkin/tree/master/examples>`_
