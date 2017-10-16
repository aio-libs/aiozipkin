import asyncio
import aiohttp

from yarl import URL


class Transport:

    def __init__(self, address, send_inteval=5, loop=None):
        self._address = URL(address).with_path("/api/v2/spans")
        self._session = aiohttp.ClientSession(loop=loop)
        self._queue = []
        self._closing = False
        self._send_interval = send_inteval
        self._loop = loop or asyncio.get_event_loop()
        self._sender_task = asyncio.ensure_future(
            self._sender_loop(), loop=loop)

    def send(self, record):
        print(record)
        data = record.asdict()
        self._queue.append(data)
        # self.http_transport(data)

    async def _sender_loop(self):
        while not self._closing:
            if len(self._queue) != 0:
                payload = self._queue[:]
                self._queue = []
                await self._send(payload)
            await asyncio.sleep(self._send_interval, loop=self._loop)

    async def _send(self, data):
        # TODO: add retries
        print(data)
        async with self._session.post(self._address, json=data) as resp:
            await resp.read()

    async def close(self):
        # TODO: make sure queue is empty before closing
        self._closing = True
        self._sender_task.cancel()
        try:
            await self._sender_task
        except asyncio.CancelledError:
            pass
        await self._session.close()
