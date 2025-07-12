from contextlib import AsyncExitStack
from functools import partial
import inspect
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Concatenate,
    Generator,
    Generic,
    Iterable,
    ParamSpec,
    TypeVar,
    Union,
    cast,
)
from fastapi import Depends, Request
from fastapi.dependencies.utils import get_dependant, solve_dependencies


T = TypeVar("T")
P = ParamSpec("P")


async def invoke_with_dependencies(
    handler: Callable[..., T | Awaitable[T]],
    request: Request,
    path: str = "/",
) -> T:
    dependant = get_dependant(path=path, call=handler)
    async with AsyncExitStack() as stack:
        solved = await solve_dependencies(
            request=request,
            dependant=dependant,
            async_exit_stack=stack,
            embed_body_fields=False,
        )
        result = handler(**solved.values)
    if inspect.isawaitable(result):
        return await result
    else:
        return cast(T, result)


def InferDepends(
    func: Union[
        Callable[P, T],
        Callable[P, Awaitable[T]],
        Callable[P, AsyncGenerator[T, Any]],
        Callable[P, Generator[T, Any, Any]],
    ],
) -> T:
    return Depends(func)

RouteEventListener = Callable[P, Callable[..., None | Awaitable]]

class RouteEvent(Generic[P]):

    def __init__(self):
        self.listeners: list[RouteEventListener[P]] = []

    def __call__(self, listener: RouteEventListener[P]):
        self.register(listener)
        return listener

    def has_listener(self) -> bool:
        return len(self.listeners) > 0

    def register(self, listener: RouteEventListener[P]):
        self.listeners.append(listener)

    def unregister(self, listener: RouteEventListener[P]):
        self.listeners.remove(listener)

    def ainvokable(self, request: Request) -> Callable[P, Awaitable]:
        async def invokable(*args: P.args, **kwargs: P.kwargs):
            for listener in self.listeners:
                await invoke_with_dependencies(
                    listener(*args, **kwargs), request
                )

        return invokable
