from contextlib import contextmanager
import pickle
import functools
import orjson
from redis import Redis
from typing import Any, Callable, Optional, TypeVar, ParamSpec, Awaitable


__all__ = [
    "cached",
    "acached",
    "redis_get",
    "redis_set",
]

T = TypeVar("T")
P = ParamSpec("P")


def cached(
    client: Redis,
    key: str | Callable[P, str],
    expire: Optional[int] = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if isinstance(key, str):
                computed_key = key
            else:
                computed_key = key(*args, **kwargs)
            cached_value = redis_get(client, computed_key)
            if cached_value is not None:
                return cached_value
            computed_value = func(*args, **kwargs)
            redis_set(client, computed_key, computed_value, expire)
            return computed_value
        return wrapper
    return decorator


def acached(
    client: Redis,
    key: str | Callable[P, str],
    expire: Optional[int] = None
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if isinstance(key, str):
                computed_key = key
            else:
                computed_key = key(*args, **kwargs)
            cached_value = redis_get(client, computed_key)
            if cached_value is not None:
                return cached_value
            computed_value = await func(*args, **kwargs)
            redis_set(client, computed_key, computed_value, expire)
            return computed_value
        return wrapper
    return decorator


def redis_set(
    redis: Redis, 
    key: str, value: Any, 
    expire: Optional[int],
    serialize: Optional[Callable[[Any], bytes]] = None
) -> None:
    if serialize is None:
        serialize = orjson.dumps
    redis.set(key, serialize(value), ex=expire)


def redis_get(
    redis: Redis, 
    key: str, 
    deserialize: Optional[Callable[[bytes], T]] = None,
) -> Optional[T]:
    if deserialize is None:
        deserialize = orjson.loads
    cached_value = redis.get(key)
    if cached_value is not None:
        if isinstance(cached_value, bytes):
            value = cached_value
        elif isinstance(cached_value, str):
            value = redis.get_encoder().encode(cached_value)
        else:
            raise ValueError("Unsupported type for cached value")
        try:
            return deserialize(value)
        except:
            return None
    return None


@contextmanager
def acquire_lock(redis: Redis, key: str, expire: int = 60):
    lock_acquired = redis.set(key, "locked", nx=True, ex=expire)
    try:
        yield bool(lock_acquired)
    finally:
        if lock_acquired:
            redis.delete(key)
