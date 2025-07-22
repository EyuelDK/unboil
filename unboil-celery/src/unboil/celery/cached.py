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
    cast,
)
from .typed import register_task

if TYPE_CHECKING:
    from redis import Redis

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
        client: "Redis",
        expire: int | None,
        key_func: Callable[..., str],
        deserialize: Callable[[bytes], T],
    ):
        self._task = task
        self._redis = client
        self._expire = expire
        self._key_func = key_func
        self._deserialize = deserialize

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
            return ResolvedCachedAsyncResult(value=self._deserialize(cached_result))


def register_cached_task(
    redis_client: "Redis",
    key: Callable[P, str],
    app: Celery | None = None,
    expire: int | None = None,
    serialize: Callable[[Any], bytes] | None = None,
    deserialize: Callable[[bytes], T] | None = None,
) -> Callable[[Callable[P, T | Awaitable[T]]], CachedTask[P, T]]:
    
    try:
        from unboil.redis import cached, acached
    except ImportError as e:
        raise ImportError(
            f"The '{register_cached_task.__name__}' feature requires the 'unboil.redis' module. "
            "Install the optional dependency with: pip install unboil-celery[redis]"
        ) from e
    
    if serialize is None:
        serialize = pickle.dumps

    if deserialize is None:
        deserialize = pickle.loads

    def decorator(main: Callable[P, T | Awaitable[T]]) -> CachedTask[P, T]:
        if inspect.iscoroutinefunction(main):
            cached_func = acached(
                client=redis_client,
                key=key,
                expire=expire,
                serialize=serialize,
                deserialize=deserialize,
            )(main)
        else:
            main = cast(Callable[P, T], main)
            cached_func = cached(
                client=redis_client,
                key=key,
                expire=expire,
                serialize=serialize,
                deserialize=deserialize,
            )(main)
        task = register_task(app=app)(cached_func)
        return CachedTask(
            task, 
            client=redis_client, 
            expire=expire, 
            key_func=key, 
            deserialize=deserialize
        )

    return decorator
