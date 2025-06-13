from typing import Any, AsyncGenerator, Awaitable, Callable, Literal, ParamSpec, Union, TypeVar
from fastapi import Depends
from sqlalchemy import Select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")
TParams = ParamSpec("TParams")

def InferDepends(
    func: Union[
        Callable[TParams, T], 
        Callable[TParams, Awaitable[T]],
        Callable[TParams, AsyncGenerator[T, Any]],
    ]) -> T:
    return Depends(func)

def make_literal(*values: str) -> Any:
    return Literal[*values]  # type: ignore


def make_union(*types: type) -> Any:
    return Union[*types]  # type: ignore


async def fetch_one(db: AsyncSession | Session, query: Select[tuple[T]]):
    if isinstance(db, AsyncSession):
        return (await db.execute(query)).scalar()
    else:
        return db.execute(query).scalar()


async def fetch_all(db: AsyncSession | Session, query: Select[tuple[T]]):   
    if isinstance(db, AsyncSession):
        return (await db.execute(query)).scalars().all()
    else:
        return db.execute(query).scalars().all()


async def save(db: AsyncSession | Session, instances: object | list[object], auto_commit: bool = True):
    if isinstance(instances, list):
        db.add_all(instances)
    else:
        db.add(instances)
    if auto_commit:
        if isinstance(db, AsyncSession):
            await db.commit()
            await db.refresh(instances)
        else:
            db.commit()
            db.refresh(instances)


async def delete(db: AsyncSession | Session, instances: object | list[object], auto_commit: bool = True):
    if isinstance(db, AsyncSession):
        await db.delete(instances)
        if auto_commit:
            await db.commit()
    else:
        db.delete(instances)
        if auto_commit:
            db.commit()
