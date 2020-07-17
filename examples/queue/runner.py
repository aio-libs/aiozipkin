import asyncio

import backend
import frontend


def run():
    loop = asyncio.get_event_loop()
    loop_run = loop.run_until_complete
    host = "127.0.0.1"
    fe_port = 9010
    be_port = 9011

    print("http://127.0.0.1:9010")

    fe_app = loop_run(frontend.make_app(host, fe_port))
    be_app = loop_run(backend.make_app(host, be_port))

    fe_handler = fe_app.make_handler()
    be_handler = be_app.make_handler()
    handlers = [fe_handler, be_handler]

    loop_run(fe_app.startup())
    loop_run(be_app.startup())
    loop_run(loop.create_server(fe_handler, host, fe_port))
    loop_run(loop.create_server(be_handler, host, be_port))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for handler in handlers:
            loop_run(handler.finish_connections())


if __name__ == "__main__":
    run()
