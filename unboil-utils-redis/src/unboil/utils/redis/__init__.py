import pickle
import functools
from redis import Redis
from typing import Callable, Optional, TypeVar, ParamSpec


P = ParamSpec("P")
R = TypeVar("R")


def redis_cached(
    client: Redis,
    key_func: Callable[P, str], 
    expire: Optional[int] = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = key_func(*args, **kwargs)
            cached = client.get(key, )
            if cached is not None:
                if isinstance(cached, bytes):
                    return pickle.loads(cached)
                if isinstance(cached, str):
                    encoder = client.get_encoder()
                    return pickle.loads(encoder.encode(cached))
            result = func(*args, **kwargs)
            client.set(key, pickle.dumps(result), ex=expire)
            return result

        return wrapper

    return decorator
