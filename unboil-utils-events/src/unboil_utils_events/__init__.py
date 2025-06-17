import asyncio
from typing import Generic, Callable, ParamSpec, TypeVar, Awaitable

__all__ = ["SyncEvent", "AsyncEvent"]

T = TypeVar("T")
P = ParamSpec("P")


class Event(Generic[P, T]):

    def __init__(self):
        self.listeners: list[Callable[P, T]] = []

    def __call__(self, listener: Callable[P, T]):
        self.register(listener)
        return listener

    def has_listener(self) -> bool:
        return len(self.listeners) > 0

    def register(self, listener: Callable[P, T]):
        self.listeners.append(listener)

    def unregister(self, listener: Callable[P, T]):
        self.listeners.remove(listener)


class SyncEvent(Event[P, T]):

    def invoke(self, *args: P.args, **kwargs: P.kwargs):
        return [listener(*args, **kwargs) for listener in self.listeners]


class AsyncEvent(Event[P, Awaitable[T]]):

    async def ainvoke(self, *args: P.args, **kwargs: P.kwargs):
        return [await listener(*args, **kwargs) for listener in self.listeners]

    async def ginvoke(self, *args: P.args, **kwargs: P.kwargs):
        return await asyncio.gather(
            *(listener(*args, **kwargs) for listener in self.listeners)
        )
