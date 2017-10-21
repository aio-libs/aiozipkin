Contributing
============

Running Tests
-------------

.. _GitHub: https://github.com/aio-libs/aiozipkin

Thanks for your interest in contributing to ``aiozipkin``, there are multiple
ways and places you can contribute, help on on documentation and tests very
appreciated.

To setup development environment, fist of all just clone repository::

    $ git clone git@github.com:aio-libs/aiozipkin.git

Create virtualenv with python3.6 (python 3.5 also supported). For example
using *virtualenvwrapper* commands could look like::

   $ cd aiozipkin
   $ mkvirtualenv --python=`which python3.5` aiozipkin


After that please install libraries required for development::

    $ pip install -r requirements-dev.txt
    $ pip install -e .

Congratulations, you are ready to run the test suite::

    $ make cov

To run individual use following command::

    $ py.test -sv tests/test_tracer.py -k test_name


Project use Docker_ for integration tests, test infrastructure will
automatically pull ``zipkin:2`` image and start server, you need to worry
about this just make sure you have Docker_ installed.


Reporting an Issue
------------------
If you have found issue with `aiozipkin` please do
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
