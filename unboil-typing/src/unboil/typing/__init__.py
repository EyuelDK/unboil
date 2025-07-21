import inspect
from typing import Awaitable, Callable, Literal, ParamSpec, TypeGuard, TypeVar, Union


T = TypeVar("T")
P = ParamSpec("P")
MaybeAsyncCallable = Callable[P, T | Awaitable[T]]


def make_literal(*values: str) -> type:
    return Literal[*values]  # type: ignore


def make_union(*types: type) -> type:
    return Union[*types]  # type: ignore


def is_async_callable[T](
    func: Callable[..., T | Awaitable[T]]
) -> TypeGuard[Callable[..., Awaitable[T]]]:
    return inspect.iscoroutinefunction(func)