import asyncio
import aiozipkin as az


async def run():
    # setup zipkin client
    zipkin_address = 'http://127.0.0.1:9411/api/v2/spans'
    endpoint = az.create_endpoint(
        'simple_service', ipv4='127.0.0.1', port=8080)

    # creates tracer object that traces all calls, if you want sample
    # only 50% just set sample_rate=0.5
    tracer = await az.create(zipkin_address, endpoint, sample_rate=1.0)

    # create and setup new trace
    with tracer.new_trace(sampled=True) as span:
        span.name('root_span')
        span.tag('span_type', 'root')
        span.kind(az.CLIENT)
        span.annotate('SELECT * FROM')
        # imitate long SQL query
        await asyncio.sleep(0.1)
        span.annotate('start end sql')

        # create child span
        with tracer.new_child(span.context) as nested_span:
            nested_span.name('nested_span_1')
            nested_span.kind(az.CLIENT)
            nested_span.tag('span_type', 'inner1')
            nested_span.remote_endpoint('remote_service_1')
            await asyncio.sleep(0.01)

        # create other child span
        with tracer.new_child(span.context) as nested_span:
            nested_span.name('nested_span_2')
            nested_span.kind(az.CLIENT)
            nested_span.remote_endpoint('remote_service_2')
            nested_span.tag('span_type', 'inner2')
            await asyncio.sleep(0.01)

    await tracer.close()
    print('-' * 100)
    print('Check zipkin UI for produced traces: http://localhost:9411/zipkin')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
