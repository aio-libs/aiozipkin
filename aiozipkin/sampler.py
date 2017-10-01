from random import Random


class Sampler:

    def __init__(self, *, sample_rate=1.0, seed=None):
        self._sample_rate = sample_rate
        self._rng = Random(seed)

    def is_sampled(self, trace_id):
        if self._sample_rate == 0.0:
            sampled = False
        else:
            sampled = self._rng.random() <= self._sample_rate
        return sampled

# TODO: implement other types of sampler for example hash trace_id
