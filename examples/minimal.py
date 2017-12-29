import asyncio
import aiozipkin as az


async def run():
    # setup zipkin client
    zipkin_address = 'http://127.0.0.1:9411'
    # address and name of current machine for better trace information
    endpoint = az.create_endpoint('minimal_example', ipv4='127.0.0.1')

    # creates tracer object that tracer all calls if you want sample
    # only 50% just set sample_rate=0.5
    tracer = az.create(zipkin_address, endpoint, sample_rate=1.0)

    # create and setup new trace
    with tracer.new_trace() as span:
        # here we just add name to the span for better search in UI
        span.name('root::span')
        # imitate long SQL query
        await asyncio.sleep(0.1)

    await tracer.close()
    print('Done, check zipkin UI')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
