import asyncio
from typing import List, Dict, Any, Optional  # flake8: noqa

import aiohttp
from yarl import URL

from .log import logger
from .mypy_types import OptLoop
from .record import Record


class Transport:

    def __init__(self, address: str, send_inteval: float=5,
                 loop: OptLoop=None) -> None:
        self._address = URL(address).with_path('/api/v2/spans')
        self._queue = []  # type: List[Dict[str, Any]]
        self._closing = False
        self._send_interval = send_inteval
        self._loop = loop or asyncio.get_event_loop()
        self._session = aiohttp.ClientSession(loop=self._loop)
        self._sender_task = asyncio.ensure_future(
            self._sender_loop(), loop=self._loop)

        self._ender = self._loop.create_future()
        self._timer = None  # type: Optional[asyncio.Future[Any]]

    def send(self, record: Record) -> None:
        data = record.asdict()
        self._queue.append(data)

    async def _sender_loop(self) -> None:
        while not self._ender.done():
            if self._queue:
                await self._send()

            await self._wait()

    async def _wait(self) -> None:
        self._timer = asyncio.ensure_future(
            asyncio.sleep(self._send_interval, loop=self._loop),
            loop=self._loop)

        await asyncio.wait([self._timer, self._ender], loop=self._loop,
                           return_when=asyncio.FIRST_COMPLETED)

    async def _send(self) -> None:
        # TODO: add retries
        data = self._queue[:]
        self._queue = []

        # TODO: add status code check
        try:
            headers = {'Content-Type': 'application/json'}
            async with self._session.post(self._address, json=data,
                                          headers=headers) as resp:
                body = await resp.text()
                if resp.status >= 300:
                    msg = 'zipkin responded with code: {} and body: {}'.format(
                        resp.status, body)
                    raise RuntimeError(msg)

        except Exception as exc:
            # that code should never fail and break application
            logger.error('Can not send spans to zipkin', exc_info=exc)

    async def close(self) -> None:
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
