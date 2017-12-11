import asyncio  # flake8: noqa
from typing import Optional, Mapping


Headers = Mapping[str, str]
OptStr = Optional[str]
OptTs = Optional[float]
OptInt = Optional[int]
OptBool = Optional[bool]
OptLoop = Optional[asyncio.AbstractEventLoop]
