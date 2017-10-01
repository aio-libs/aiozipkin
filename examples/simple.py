import aiozipkin
import time


def main():
    zipkin_address = "http://localhost:9411/api/v2/spans"
    endpoint = aiozipkin.create_endpoint(
        "service_name2", ipv4="127.0.0.1", port=8080)
    tracer = aiozipkin.create(zipkin_address, endpoint)

    with tracer.new_trace() as span:
        span.name("root_span")
        span.tag("span_type", "root")
        span.kind("CLIENT")
        span.annotate("start sql")
        time.sleep(0.1)
        span.annotate("start end sql")

        with tracer.new_child(span.context) as nested_span:
            nested_span.name("nested_span1")
            nested_span.kind("CLIENT")
            nested_span.tag("span_type", "inner1")
            nested_span.remote_endpoint("service", ipv4="127.0.0.1", port=9001)
            time.sleep(0.01)

        with tracer.new_child(span.context) as nested_span:
            nested_span.name("nested_span2")
            nested_span.kind("CLIENT")
            nested_span.remote_endpoint("service", ipv4="127.0.0.1", port=9002)
            nested_span.tag("span_type", "inner2")
            time.sleep(0.01)


if __name__ == "__main__":
    main()
