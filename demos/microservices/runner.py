import asyncio

import service_a
import service_b
import service_c
import service_d
import service_e


def run():
    loop = asyncio.get_event_loop()
    apps = [
        service_a.make_app(),
        service_b.make_app(),
        service_c.make_app(),
        service_d.make_app(),
        service_e.make_app(),
    ]
    handlers = []
    for i, app in enumerate(apps):
        handler = app.make_handler()
        handlers.append(handler)
        loop.run_until_complete(loop.create_server(
            handler, '127.0.0.1', 9001 + i))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for handler in handlers:
            loop.run_until_complete(handler.finish_connections())


if __name__ == '__main__':
    run()
