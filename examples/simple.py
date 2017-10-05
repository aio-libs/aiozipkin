import asyncio
import aiozipkin


async def run():
    zipkin_address = "http://localhost:9411/api/v2/spans"
    endpoint = aiozipkin.create_endpoint(
        "simple_service", ipv4="127.0.0.1", port=8080)
    tracer = aiozipkin.create(zipkin_address, endpoint)

    with tracer.new_trace(sampled=True) as span:
        span.name("root_span")
        span.tag("span_type", "root")
        span.kind("CLIENT")
        span.annotate("SELECT * FROM")

        await asyncio.sleep(0.1)
        span.annotate("start end sql")

        with tracer.new_child(span.context) as nested_span:
            nested_span.name("nested_span_1")
            nested_span.kind("CLIENT")
            nested_span.tag("span_type", "inner1")
            nested_span.remote_endpoint("remote_service_1")
            await asyncio.sleep(0.01)

        with tracer.new_child(span.context) as nested_span:
            nested_span.name("nested_span_2")
            nested_span.kind("CLIENT")
            nested_span.remote_endpoint("remote_service_2")
            nested_span.tag("span_type", "inner2")
            await asyncio.sleep(0.01)

        await asyncio.sleep(30)
        await tracer.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
