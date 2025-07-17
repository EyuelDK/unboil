import pickle
import functools
import asyncio
from redis import Redis
from typing import Callable, Optional, TypeVar, ParamSpec, Awaitable, Union


P = ParamSpec("P")
R = TypeVar("R")


def redis_cached(
    client: Redis,
    keyf: Callable[P, str], 
    expire: Optional[int] = None
) -> Callable[[Callable[P, Union[R, Awaitable[R]]]], Callable[P, Union[R, Awaitable[R]]]]:

    def get_cached(key: str) -> R | None:
        cached = client.get(key)
        if cached is not None:
            if isinstance(cached, bytes):
                return pickle.loads(cached)
            if isinstance(cached, str):
                encoder = client.get_encoder()
                return pickle.loads(encoder.encode(cached))
        return None

    def set_cached(key: str, value: R) -> None:
        client.set(key, pickle.dumps(value), ex=expire)

    def decorator(func: Callable[P, R]) -> Callable[P, Union[R, Awaitable[R]]]:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                key = keyf(*args, **kwargs)
                cached = get_cached(key)
                if cached is not None:
                    return cached
                result = await func(*args, **kwargs)
                set_cached(key, result)
                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                key = keyf(*args, **kwargs)
                cached = get_cached(key)
                if cached is not None:
                    return cached
                result = func(*args, **kwargs)
                set_cached(key, result)
                return result
            return sync_wrapper

    return decorator
