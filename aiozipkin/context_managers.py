from collections.abc import Awaitable as AbcAwaitable
from typing import (TypeVar, Optional, Generator, Any, Type,
                    AsyncContextManager, Generic, Awaitable)
from types import TracebackType


T = TypeVar('T', bound=AsyncContextManager)


class _ContextManager(Generic[T], AsyncContextManager, AbcAwaitable):

    __slots__ = ('_coro', '_obj')

    def __init__(self, coro: Awaitable[T]) -> None:
        self._coro = coro  # type: Awaitable[T]
        self._obj = None  # type: Optional[T]

    def __await__(self) -> Generator[Any, None, T]:
        return self._coro.__await__()

    async def __aenter__(self) -> T:
        self._obj = await self._coro
        t = await self._obj.__aenter__()  # type: T
        return t

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc: Optional[BaseException],
                        tb: Optional[TracebackType]) -> Optional[bool]:
        if self._obj is None:
            raise RuntimeError('__aexit__ called before __aenter__')
        return await self._obj.__aexit__(exc_type, exc, tb)
