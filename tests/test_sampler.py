from aiozipkin.sampler import Sampler


def test_sample_always() -> None:
    sampler = Sampler(sample_rate=1.0)
    trace_id = "bde15168450e7097008c7aab41c27ade"
    assert sampler.is_sampled(trace_id)
    assert sampler.is_sampled(trace_id)
    assert sampler.is_sampled(trace_id)


def test_sample_never() -> None:
    sampler = Sampler(sample_rate=0.0)
    trace_id = "bde15168450e7097008c7aab41c27ade"
    assert not sampler.is_sampled(trace_id)
    assert not sampler.is_sampled(trace_id)
    assert not sampler.is_sampled(trace_id)


def test_sample_with_rate() -> None:
    sampler = Sampler(sample_rate=0.3, seed=123)
    trace_id = "bde15168450e7097008c7aab41c27ade"
    assert sampler.is_sampled(trace_id)
    assert sampler.is_sampled(trace_id)
    assert not sampler.is_sampled(trace_id)
