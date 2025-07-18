import pickle
import functools
from redis import Redis
from typing import Any, Callable, Optional, TypeVar, ParamSpec, Awaitable


__all__ = [
    "cached",
    "acached",
]

P = ParamSpec("P")
R = TypeVar("R")


def cached(
    client: Redis,
    key: str | Callable[P, str],
    expire: Optional[int] = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if isinstance(key, str):
                computed_key = key
            else:
                computed_key = key(*args, **kwargs)
            cached = _redis_get(client, computed_key)
            if cached is not None:
                return cached
            result = func(*args, **kwargs)
            _redis_set(client, computed_key, result, expire)
            return result
        return wrapper
    return decorator


def acached(
    client: Redis,
    key: str | Callable[P, str],
    expire: Optional[int] = None
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if isinstance(key, str):
                computed_key = key
            else:
                computed_key = key(*args, **kwargs)
            cached = _redis_get(client, computed_key)
            if cached is not None:
                return cached
            result = await func(*args, **kwargs)
            _redis_set(client, computed_key, result, expire)
            return result
        return wrapper
    return decorator


def _redis_set(client: Redis, key: str, value: Any, expire: Optional[int]) -> None:
    client.set(key, pickle.dumps(value), ex=expire)


def _redis_get(client: Redis, key: str) -> Optional[Any]:
    cached = client.get(key)
    if cached is not None:
        if isinstance(cached, bytes):
            data = cached
        elif isinstance(cached, str):
            data = client.get_encoder().encode(cached)
        else:
            raise ValueError("Unsupported type for cached value")
        try:
            return pickle.loads(data)
        except:
            return None
    return None