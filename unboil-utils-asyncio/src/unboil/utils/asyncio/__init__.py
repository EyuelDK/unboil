
import asyncio
from typing import Awaitable, Iterable, TypeVar


T = TypeVar("T")

def with_semaphore(
    semaphore: asyncio.Semaphore, 
    tasks: Iterable[Awaitable[T]]
) -> Iterable[Awaitable[T]]:
    async def sem_task(task: Awaitable[T]) -> T:
        async with semaphore:
            return await task
    return (sem_task(task) for task in tasks)
    
