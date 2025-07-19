import pickle
from dataclasses import dataclass
from celery import Task, Celery
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Generic, TypeVar, ParamSpec, Union

from unboil.celery import register_task

if TYPE_CHECKING:
    from redis import Redis


__all__ = [
    "register_task_with_cache",
    "CachedTask",
    "CachedAsyncResult",
]


T = TypeVar("T")
P = ParamSpec("P")
SyncOrAsyncCallable = Callable[P, T | Awaitable[T]]


@dataclass(kw_only=True)
class CachedAsyncResult(Generic[T]):
    complete: bool
    result: T | None

class CachedTask(Task, Generic[P, T]):
        
    def _init(
        self, 
        redis: Redis, 
        key_func: Callable[..., str], 
        expire: int | None = None
    ):
        self.redis = redis
        self.expire = expire
        self.key_func = key_func

    def delay_with_cache(self, *args: P.args, **kwargs: P.kwargs) -> CachedAsyncResult[T]:
        key = self.key_func(*args, **kwargs)
        cached_result = self.redis.get(key)
        if cached_result is None:
            self.delay(*args, **kwargs)
            return CachedAsyncResult(complete=False, result=None)
        else:
            if isinstance(cached_result, bytes):
                cached_result = cached_result
            elif isinstance(cached_result, str):
                cached_result = self.redis.get_encoder().encode(cached_result)
            else:
                raise ValueError("Unsupported type for cached value")
            return CachedAsyncResult(complete=True, result=pickle.loads(cached_result))
     
    def on_success(self, retval: T, task_id: str, args: Any, kwargs: Any) -> None:
        key = self.key_func(*args, **kwargs)
        self.redis.set(key, pickle.dumps(retval), ex=self.expire)
        

def register_task_with_cache(
    redis: Redis,
    key: Callable[P, str],
    app: Celery | None = None,
    expire: int | None = None,
) -> Callable[[SyncOrAsyncCallable[P, T]], CachedTask[P, T]]:
    def decorator(main: SyncOrAsyncCallable[P, T]) -> CachedTask[P, T]:
        task = register_task(app, base=CachedTask[P, T])(main)
        task._init(redis, key, expire)
        return task
    return decorator