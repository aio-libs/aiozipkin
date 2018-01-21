import asyncio
import logging

from aiohttp import web

import service_a
import service_b
import service_c
import service_d
import service_e


async def start_app(service, host, port):
    app = await service.make_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner


# TODO: rework after aiohttp 3.0.0 release
def run():
    host = '127.0.0.1'
    loop = asyncio.get_event_loop()
    services = [service_a, service_b, service_c, service_d, service_e]
    runners = []
    for i, service in enumerate(services):
        port = 9001 + i
        runner = loop.run_until_complete(start_app(service, host, port))
        runners.append(runner)

    print("Open in browser: http://127.0.0.1:9001")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for runner in runners:
            loop.run_until_complete(runner.cleanup())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run()
