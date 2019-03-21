import asyncio
import gc

import aiohttp
from aiohttp import web
from aiozipkin.helpers import create_endpoint, TraceContext
from aiozipkin.sampler import Sampler
from aiozipkin.tracer import Tracer
from aiozipkin.transport import StubTransport
from async_generator import yield_, async_generator

import pytest
from aiohttp.test_utils import TestServer


@pytest.fixture(scope='session')
def event_loop():
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    gc.collect()
    loop.close()


@pytest.fixture(scope='session')
def loop(event_loop):
    return event_loop


@pytest.fixture
def fake_transport():
    transport = StubTransport()
    return transport


@pytest.fixture(name='tracer')
def tracer_fixture(fake_transport):
    sampler = Sampler(sample_rate=1.0)
    endpoint = create_endpoint('test_service', ipv4='127.0.0.1', port=8080)
    # TODO: use context manger at some point
    return Tracer(fake_transport, sampler, endpoint)


@pytest.fixture
def context():
    context = TraceContext(
        trace_id='6f9a20b5092fa5e144fd15cc31141cd4',
        parent_id=None,
        span_id='41baf1be2fb9bfc5',
        sampled=True,
        debug=False,
        shared=True)
    return context


@pytest.fixture
@async_generator
async def client(loop):
    async with aiohttp.ClientSession(loop=loop) as client:
        await yield_(client)


class FakeZipkin:

    def __init__(self, loop):
        self.next_errors = []
        self.app = web.Application()
        self.app.router.add_post('/api/v2/spans', self.spans_handler)
        self.port = None
        self._loop = loop
        self._received_data = []
        self._wait_count = None
        self._wait_fut = None

    @property
    def url(self):
        return 'http://127.0.0.1:%s/api/v2/spans' % self.port

    async def spans_handler(self, request: web.Request) -> web.Response:
        if len(self.next_errors) > 0:
            err = self.next_errors.pop(0)
            if err == 'disconnect':
                request.transport.close()
                await asyncio.sleep(1, loop=self._loop)
            elif err == 'timeout':
                await asyncio.sleep(60, loop=self._loop)
            return web.HTTPInternalServerError()

        data = await request.json()
        if self._wait_count is not None:
            self._wait_count -= 1
        self._received_data.append(data)
        if self._wait_fut is not None and self._wait_count == 0:
            self._wait_fut.set_result(None)

        return aiohttp.web.Response(text='', status=200)

    def get_received_data(self) -> list:
        data = self._received_data
        self._received_data = []
        return data

    def wait_data(self, count):
        self._wait_fut = asyncio.Future(loop=self._loop)
        self._wait_count = count
        return self._wait_fut


@pytest.fixture
@async_generator
async def fake_zipkin(loop):
    zipkin = FakeZipkin(loop=loop)

    server = TestServer(zipkin.app, loop=loop)
    await server.start_server()
    zipkin.port = server.port

    await yield_(zipkin)

    await server.close()


pytest_plugins = ['docker_fixtures']
