from random import Random
from typing import Optional


class Sampler:

    def __init__(self, *, sample_rate: float=1.0,
                 seed: Optional[int]=None) -> None:
        self._sample_rate = sample_rate
        self._rng = Random(seed)

    def is_sampled(self, trace_id: str) -> bool:
        if self._sample_rate == 0.0:
            sampled = False
        else:
            sampled = self._rng.random() <= self._sample_rate
        return sampled

# TODO: implement other types of sampler for example hash trace_id
