import uuid
import inspect
from functools import wraps
from typing import Any, Awaitable, Callable, ParamSpec, TypeVar
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler


__all__ = [
    "watch",
    "awatch",
]

T  = TypeVar("T")
P = ParamSpec("P")

_sync_scheduler = BackgroundScheduler()
_sync_scheduler.start()

_async_scheduler = AsyncIOScheduler()
_async_scheduler.start()


def watch(
    tick: Callable[P, None], 
    interval: int = 5,
):
    
    def decorator(main: Callable[P, T]) -> Callable[P, T]:

        @wraps(main)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            
            def func() -> None:
                tick(*args, **kwargs)

            job_id = str(uuid.uuid4())
            job = _sync_scheduler.add_job(
                func=func,
                trigger="interval",
                id=job_id,
                seconds=interval,
            )
            try:
                return main(*args, **kwargs)
            finally:
                try:
                    _sync_scheduler.remove_job(job.id)
                except JobLookupError:
                    pass

        return wrapper

    return decorator


def awatch(
    tick: Callable[P, None | Awaitable[None]], 
    interval: int = 5,
):

    def decorator(main: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:

        @wraps(main)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            
            async def func():
                if inspect.iscoroutinefunction(tick):
                    await tick(*args, **kwargs)
                else:
                    tick(*args, **kwargs)
            
            job_id = str(uuid.uuid4())
            job = _async_scheduler.add_job(
                func=func,
                trigger="interval",
                id=job_id,
                seconds=interval,
            )
            try:
                return await main(*args, **kwargs)
            finally:
                try:
                    _async_scheduler.remove_job(job.id)
                except JobLookupError:
                    pass

        return wrapper

    return decorator