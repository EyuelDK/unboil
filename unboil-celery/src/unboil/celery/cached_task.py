import inspect
import pickle
from dataclasses import dataclass
from celery import Task, Celery, shared_task
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Generic,
    Literal,
    TypeVar,
    ParamSpec,
    Union,
)

from .typed_task import register_task, TypedTask

if TYPE_CHECKING:
    from redis import Redis


__all__ = [
    "register_cached_task",
    "CachedTask",
    "CachedAsyncResult",
]


T = TypeVar("T")
P = ParamSpec("P")
SyncOrAsyncCallable = Callable[P, T | Awaitable[T]]


@dataclass(kw_only=True)
class ResolvedCachedAsyncResult(Generic[T]):
    status: Literal["resolved"] = "resolved"
    value: T


@dataclass(kw_only=True)
class PendingCachedAsyncResult(Generic[T]):
    status: Literal["pending"] = "pending"


CachedAsyncResult = Union[ResolvedCachedAsyncResult[T], PendingCachedAsyncResult[T]]


class CachedTask(Generic[P, T]):

    def __init__(
        self,
        task: Task,
        redis: "Redis",
        expire: int | None,
        key_func: Callable[..., str],
    ):
        self._task = task
        self._redis = redis
        self._expire = expire
        self._key_func = key_func

    def invalidate(self, *args: P.args, **kwargs: P.kwargs) -> None:
        key = self._key_func(*args, **kwargs)
        self._redis.delete(key)

    def try_delay(self, *args: P.args, **kwargs: P.kwargs) -> CachedAsyncResult[T]:
        key = self._key_func(*args, **kwargs)
        cached_result = self._redis.get(key)
        if cached_result is None:
            self._task.delay(*args, **kwargs)
            return PendingCachedAsyncResult()
        else:
            if isinstance(cached_result, bytes):
                cached_result = cached_result
            elif isinstance(cached_result, str):
                cached_result = self._redis.get_encoder().encode(cached_result)
            else:
                raise ValueError("Unsupported type for cached value")
            return ResolvedCachedAsyncResult(value=pickle.loads(cached_result))


def register_cached_task(
    redis: "Redis",
    key: Callable[P, str],
    app: Celery | None = None,
    expire: int | None = None,
) -> Callable[[SyncOrAsyncCallable[P, T]], CachedTask[P, T]]:
    from unboil.redis import cached, acached

    def decorator(main: SyncOrAsyncCallable[P, T]) -> CachedTask[P, T]:
        if not inspect.iscoroutinefunction(main):
            cached_main = cached(client=redis, key=key, expire=expire)(main)
        else:
            cached_main = acached(client=redis, key=key, expire=expire)(main)
        task = register_task(app=app)(cached_main)
        return CachedTask(task, redis=redis, expire=expire, key_func=key)

    return decorator
