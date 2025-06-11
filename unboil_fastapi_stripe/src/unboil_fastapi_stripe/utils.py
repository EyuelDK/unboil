from typing import Any, Literal, Union, TypeVar
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


def make_literal(*values: str) -> Any:
    return Literal[*values]  # type: ignore


def make_union(*types: type) -> Any:
    return Union[*types]  # type: ignore


async def fetch_one(db: AsyncSession, query: Select[tuple[T]]):
    return (await db.execute(query)).scalar()


async def fetch_all(db: AsyncSession, query: Select[tuple[T]]):
    return list((await db.execute(query)).scalars().all())


async def save(db: AsyncSession, instances: object | list[object], auto_commit: bool = True):
    if isinstance(instances, list):
        db.add_all(instances)
    else:
        db.add(instances)
    if auto_commit:
        await db.commit()
        await db.refresh(instances)


async def delete(db: AsyncSession, instances: object | list[object], auto_commit: bool = True):
    await db.delete(instances)
    if auto_commit:
        await db.commit()
