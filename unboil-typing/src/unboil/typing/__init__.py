import inspect
from typing import (
    Awaitable,
    Callable,
    Literal,
    ParamSpec,
    TypeGuard,
    TypeVar,
    Union,
    overload,
)


T = TypeVar("T")
P = ParamSpec("P")
AsyncCallable = Callable[P, Awaitable[T]]
MaybeAsyncCallable = AsyncCallable[P, T] | Callable[P, T]


def make_literal(*values: str) -> type:
    return Literal[*values]  # type: ignore


def make_union(*types: type) -> type:
    return Union[*types]  # type: ignore


@overload
def is_async_callable(func: AsyncCallable[P, T]) -> TypeGuard[AsyncCallable[P, T]]: ...


@overload
def is_async_callable(func: Callable[P, T]) -> TypeGuard[Callable[P, T]]: ...


def is_async_callable(
    func: MaybeAsyncCallable[P, T],
) -> TypeGuard[AsyncCallable[P, T]] | TypeGuard[Callable[P, T]]:
    return inspect.iscoroutinefunction(func)
