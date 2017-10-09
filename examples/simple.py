import asyncio
import aiozipkin as az


async def run():
    # setup zipkin client
    zipkin_address = "http://localhost:9411/api/v2/spans"
    endpoint = az.create_endpoint(
        "simple_service", ipv4="127.0.0.1", port=8080)
    tracer = az.create(zipkin_address, endpoint)

    # create and setup new trace
    with tracer.new_trace(sampled=True) as span:
        span.name("root_span")
        span.tag("span_type", "root")
        span.kind(az.CLIENT)
        span.annotate("SELECT * FROM")
        # imitate long SQL query
        await asyncio.sleep(0.1)
        span.annotate("start end sql")

        # create child span
        with tracer.new_child(span.context) as nested_span:
            nested_span.name("nested_span_1")
            nested_span.kind(az.CLIENT)
            nested_span.tag("span_type", "inner1")
            nested_span.remote_endpoint("remote_service_1")
            await asyncio.sleep(0.01)

        # create other child span
        with tracer.new_child(span.context) as nested_span:
            nested_span.name("nested_span_2")
            nested_span.kind(az.CLIENT)
            nested_span.remote_endpoint("remote_service_2")
            nested_span.tag("span_type", "inner2")
            await asyncio.sleep(0.01)

        await asyncio.sleep(30)
        await tracer.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
