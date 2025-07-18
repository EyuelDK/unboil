from dataclasses import dataclass
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import Select, func, select
from typing import AsyncIterable, Generic, Sequence, TypeVar

T = TypeVar("T")
TTuple = TypeVar("TTuple", bound=tuple)


async def fetch_one(db: AsyncSession | Session, query: Select[tuple[T]]) -> T | None:
    if isinstance(db, AsyncSession):
        return (await db.execute(query)).scalar()
    else:
        return db.execute(query).scalar()


async def fetch_all(db: AsyncSession | Session, query: Select[tuple[T]]) -> Sequence[T]:
    if isinstance(db, AsyncSession):
        return (await db.execute(query)).scalars().all()
    else:
        return db.execute(query).scalars().all()


async def count(db: AsyncSession | Session, query: Select[TTuple]) -> int:
    count_query = select(func.count()).select_from(query.alias())
    return await fetch_one(db, count_query) or 0


async def save(
    db: AsyncSession | Session,
    instances: list[object],
    auto_commit: bool = True,
) -> None:
    db.add_all(instances)
    if auto_commit:
        if isinstance(db, AsyncSession):
            await db.commit()
            for instance in instances:
                await db.refresh(instance)
        else:
            db.commit()
            for instance in instances:
                db.refresh(instance)


async def delete(
    db: AsyncSession | Session,
    instances: list[object],
    auto_commit: bool = True,
) -> None:
    if isinstance(db, AsyncSession):
        for instance in instances:
            await db.delete(instance)
        if auto_commit:
            await db.commit()
    else:
        for instance in instances:
            db.delete(instance)
        if auto_commit:
            db.commit()


@dataclass(kw_only=True)
class PaginatedResult(Generic[T]):
    has_more: bool
    total: int
    offset: int
    limit: int | None
    items: list[T]

    @property
    def current_page(self) -> int:
        if self.limit is None:
            return 1
        return math.ceil((self.offset - 1) / self.limit) + 1

    @property
    def total_pages(self) -> int:
        if self.limit is None:
            return 1
        return math.ceil((self.total - 1) / self.limit) + 1


async def paginate(
    db: AsyncSession | Session,
    query: Select[tuple[T]],
    offset: int = 0,
    limit: int | None = None,
) -> PaginatedResult[T]:
    total = await count(db=db, query=query)
    query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit + 1)
    results = await fetch_all(db=db, query=query)
    has_more = limit is not None and len(results) > limit
    return PaginatedResult(
        has_more=has_more,
        total=total or 0,
        limit=limit,
        offset=offset,
        items=list(results[:-1]) if has_more else list(results),
    )


async def iter_pages(
    db: AsyncSession | Session,
    query: Select[tuple[T]],
    page_size: int = 1000,
) -> AsyncIterable[PaginatedResult[T]]:
    
    offset = 0
    total = await count(db=db, query=query)
    while True:
        query = query.offset(offset)
        query = query.limit(page_size + 1)
        results = await fetch_all(db=db, query=query)
        has_more = len(results) > page_size
        yield PaginatedResult(
            has_more=has_more,
            total=total or 0,
            limit=page_size,
            offset=offset,
            items=list(results[:-1]) if has_more else list(results),
        )
        if not has_more:
            break
        offset += page_size