from random import Random

from .mypy_types import OptInt


class Sampler:

    def __init__(self, *, sample_rate: float=1.0, seed: OptInt=None) -> None:
        self._sample_rate = sample_rate
        self._rng = Random(seed)

    def is_sampled(self, trace_id: str) -> bool:
        if self._sample_rate == 0.0:
            sampled = False
        else:
            sampled = self._rng.random() <= self._sample_rate
        return sampled

# TODO: implement other types of sampler for example hash trace_id
