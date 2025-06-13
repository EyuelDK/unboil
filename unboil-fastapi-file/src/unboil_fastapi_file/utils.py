from typing import Any, Awaitable, Callable, Generic, ParamSpec, TypeVar, Literal, Union
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")
TParams = ParamSpec("TParams")

class Signal(Generic[TParams, T]):
    
    def __init__(self):
        self.listeners: list[Callable[TParams, T]] = []

    def register(self, listener: Callable[TParams, T]):
        self.listeners.append(listener)

    def unregister(self, listener: Callable[TParams, T]):
        self.listeners.remove(listener)


class SyncSignal(Signal[TParams, T]):
    
    def invoke(self, *args: TParams.args, **kwargs: TParams.kwargs):
        for listener in self.listeners:
            listener(*args, **kwargs)

class AsyncSignal(Signal[TParams, Awaitable[T]]):
    
    async def ainvoke(self, *args: TParams.args, **kwargs: TParams.kwargs):
        for listener in self.listeners:
            await listener(*args, **kwargs)
            

def make_literal(*values: str) -> Any:
    return Literal[*values]  # type: ignore


def make_union(*types: type) -> Any:
    return Union[*types]  # type: ignore


async def fetch_one(db: AsyncSession, query: Select[tuple[T]]):
    return (await db.execute(query)).scalar()


async def fetch_all(db: AsyncSession, query: Select[tuple[T]]):
    return (await db.execute(query)).scalars().all()


async def save(db: AsyncSession, instance: object):
    db.add(instance)
    await db.commit()
    await db.refresh(instance)