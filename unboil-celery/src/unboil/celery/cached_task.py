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
from redis import Redis
from unboil.redis import cached, acached
from unboil.typing import MaybeAsyncCallable, is_async_callable


__all__ = [
    "register_cached_task",
    "CachedTask",
    "CachedAsyncResult",
]


T = TypeVar("T")
P = ParamSpec("P")


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
    redis_client: "Redis",
    key: Callable[P, str],
    app: Celery | None = None,
    expire: int | None = None,
    serialize: Callable[[Any], bytes] | None = None,
    deserialize: Callable[[bytes], T] | None = None,
) -> Callable[[MaybeAsyncCallable[P, T]], CachedTask[P, T]]:

    def decorator(main: MaybeAsyncCallable[P, T]) -> CachedTask[P, T]:
        if not is_async_callable(main):
            x = main
            cached_func = cached(
                client=redis_client,
                key=key,
                expire=expire,
                serialize=serialize,
                deserialize=deserialize,
            )(main)
        else:
            cached_func = acached(
                client=redis_client,
                key=key,
                expire=expire,
                serialize=serialize,
                deserialize=deserialize,
            )(main)
        task = register_task(app=app)(cached_func)
        return CachedTask(task, redis=redis_client, expire=expire, key_func=key)

    return decorator
