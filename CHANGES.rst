CHANGES
=======

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://pip.pypa.io/en/latest/development/#adding-a-news-entry
    we named the news folder "changes".

    WARNING: Don't drop the next directive!

.. towncrier release notes start

1.1.0 (2021-05-17)
==================

Bugfixes
--------

- Expect trace request context to be of SimpleNamespace type.
  `#385 <https://github.com/aio-libs/aiohttp/issues/385>`_


----


1.0.0 (2020-11-06)
==================

Bugfixes
--------

- Support Python 3.8 and Python 3.9
  `#259 <https://github.com/aio-libs/aiohttp/issues/259>`_


----


0.7.1 (2020-09-20)
==================

Bugfixes
--------

- Fix `Manifest.in` file; add `CHANGES.rst` to the Source Tarball.


0.7.0 (2020-07-17)
==================

Features
--------

- Add support of AWS X-Ray trace id format.
  `#273 <https://github.com/aio-libs/aiohttp/issues/273>`_


----


0.6.0 (2019-10-12)
------------------
* Add context var support for python3.7 aiohttp instrumentation #187
* Single header tracing support #189
* Add retries and batches to transport (thanks @konstantin-stepanov)
* Drop python3.5 support #238
* Use new typing syntax in codebase #237


0.5.0 (2018-12-25)
------------------
* More strict typing configuration is used #147
* Fixed bunch of typos in code and docs #151 #153 (thanks @deejay1)
* Added interface for Transport #155 (thanks @deejay1)
* Added create_custom helper for easer tracer configuration #160 (thanks @deejay1)
* Added interface for Sampler #160 (thanks @deejay1)
* Added py.typed marker


0.4.0 (2018-07-11)
------------------
* Add more coverage with typing #147
* Breaking change: typo send_inteval => send_interval #144 (thanks @gugu)
* Breaking change: do not append api/v2/spans to the zipkin dress #150


0.3.0 (2018-06-13)
------------------
* Add support http.route tag for aiohttp #138
* Make zipkin address builder more permissive #141 (thanks @dsantosfff)


0.2.0 (2018-03-03)
------------------
* Breaking change: az.create is coroutine now #114
* Added context manger for tracer object #114
* Added more mypy types #117


0.1.1 (2018-01-26)
------------------
* Added new_child helper method #83


0.1.0 (2018-01-21)
------------------
After few months of work and beta releases here are basic features:

* Initial release.
* Implemented zipkin v2 protocol with HTTP transport
* Added jaeger support
* Added stackdriver support
* Added aiohttp server support
* Added aiohttp 3.0.0 client tracing support
* Added examples and demos
