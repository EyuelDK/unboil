import asyncio
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
        wrapper = main
        if inspect.iscoroutinefunction(main):

            def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                return asyncio.run(main(*args, **kwargs))

        task_decorator = shared_task if app is None else app.task
        return cast(TypedTask[P], task_decorator(**kwargs)(wrapper))

    return decorator
