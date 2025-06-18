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


class RouteEvent(Generic[P]):

    def __init__(self):
        self.listeners: list[Callable[P, None | Awaitable]] = []

    def __call__(self, listener: Callable[P, None | Awaitable]):
        self.register(listener)
        return listener

    def has_listener(self) -> bool:
        return len(self.listeners) > 0

    def register(self, listener: Callable[P, None | Awaitable]):
        self.listeners.append(listener)

    def unregister(self, listener: Callable[P, None | Awaitable]):
        self.listeners.remove(listener)

    def ainvokable(self, request: Request) -> Callable[P, Awaitable]:
        async def invokable(*args: P.args, **kwargs: P.kwargs):
            for listener in self.listeners:
                signature = inspect.signature(listener)
                bound = signature.bind_partial(*args, **kwargs)
                await invoke_with_dependencies(
                    partial(listener, *bound.args, **bound.kwargs), request
                )

        return invokable
