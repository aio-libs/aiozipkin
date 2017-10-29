import asyncio
import aiohttp

from yarl import URL
from .log import logger


class Transport:

    def __init__(self, address, send_inteval=5, loop=None):
        self._address = URL(address).with_path('/api/v2/spans')
        self._session = aiohttp.ClientSession(loop=loop)
        self._queue = []
        self._closing = False
        self._send_interval = send_inteval
        self._loop = loop or asyncio.get_event_loop()
        self._sender_task = asyncio.ensure_future(
            self._sender_loop(), loop=loop)
        self._ender = self._loop.create_future()
        self._timer = None

    def send(self, record):
        data = record.asdict()
        self._queue.append(data)

    async def _sender_loop(self):
        while not self._ender.done():
            if self._queue:
                await self._send()

            self._timer = asyncio.ensure_future(
                asyncio.sleep(self._send_interval, loop=self._loop))
            await next(asyncio.as_completed([self._timer, self._ender]))

    async def _send(self):
        # TODO: add retries
        data = self._queue[:]
        self._queue = []

        # TODO: add status code check
        try:
            async with self._session.post(self._address, json=data) as resp:
                await resp.read()
                if resp.status >= 300:
                    msg = 'Remote zipkin responded with {} code'.format(
                        resp.status)
                    raise RuntimeError(msg)

        except Exception as exc:
            # that code should never fail
            logger.error('Can not send spans to zipking', exc_info=exc)

    async def close(self):
        # TODO: make sure queue is empty before closing
        if self._closing:
            return

        self._closing = True
        self._ender.set_result(None)

        await self._sender_task
        await self._send()
        await self._session.close()

        if self._timer is not None:
            self._timer.cancel()
            try:
                await self._timer
            except asyncio.CancelledError:
                pass
