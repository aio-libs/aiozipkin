Contributing
============

Setting Development Environment
-------------------------------

.. _GitHub: https://github.com/aio-libs/aiozipkin

Thanks for your interest in contributing to ``aiozipkin``, there are multiple
ways and places you can contribute, help on on documentation and tests is very
appreciated.

To setup development environment, fist of all just clone repository:

.. code-block:: bash

    $ git clone git@github.com:aio-libs/aiozipkin.git

Create virtualenv with python3.6+. For example
using *virtualenvwrapper* commands could look like:

.. code-block:: bash

   $ cd aiozipkin
   $ mkvirtualenv --python=`which python3.6` aiozipkin


After that please install libraries required for development:

.. code-block:: bash

    $ pip install -r requirements-dev.txt
    $ pip install -e .


Running Tests
-------------
Congratulations, you are ready to run the test suite:

.. code-block:: bash

    $ make cov

To run individual test use following command:

.. code-block:: bash

    $ py.test -sv tests/test_tracer.py -k test_name


Project uses Docker_ for integration tests, test infrastructure will
automatically pull ``zipkin:2`` or ``jaegertracing/all-in-one:1.0.0`` image
and start server, you don't to worry about this just make sure you
have Docker_ installed.


Reporting an Issue
------------------
If you have found an issue with `aiozipkin` please do
not hesitate to file an issue on the GitHub_ project. When filing your
issue please make sure you can express the issue with a reproducible test
case.

When reporting an issue we also need as much information about your environment
that you can include. We never know what information will be pertinent when
trying narrow down the issue. Please include at least the following
information:

* Version of `aiozipkin` and `python`.
* Version `zipkin` server.
* Platform you're running on (OS X, Linux).

.. _Docker: https://docs.docker.com/engine/installation/
