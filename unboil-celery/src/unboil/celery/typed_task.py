import asyncio
import functools
import inspect
from celery import Celery, Task, shared_task
from celery.result import AsyncResult
from typing import (
    TYPE_CHECKING,
    Generic,
    ParamSpec,
    Callable,
    Awaitable,
    Any,
    TypeVar,
    cast,
)

__all__ = [
    "TypedTask",
    "register_task",
]


T = TypeVar("T")
P = ParamSpec("P")
SyncOrAsyncCallable = Callable[P, T | Awaitable[T]]


class TypedTask(Task, Generic[P]):

    if TYPE_CHECKING:

        def __call__(self, *args: P.args, **kwargs: P.kwargs): ...
        def delay(self, *args: P.args, **kwargs: P.kwargs) -> AsyncResult: ...


def register_task(
    app: Celery | None = None, **kwargs
) -> Callable[[SyncOrAsyncCallable[P, T]], TypedTask[P]]:

    def decorator(main: SyncOrAsyncCallable[P, T]) -> TypedTask[P]:
        if not inspect.iscoroutinefunction(main):
            wrapped = main
        else:
            def async_caller(*args: P.args, **kwargs: P.kwargs) -> Any:
                return asyncio.run(main(*args, **kwargs))
            wrapped = functools.wraps(main)(async_caller)
        task_decorator = shared_task if app is None else app.task
        return cast(TypedTask[P], task_decorator(**kwargs)(wrapped))

    return decorator
