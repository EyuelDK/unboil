from fastapi import Request
from typing import Any, Literal, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select

T = TypeVar("T")

async def fetch_one(db: AsyncSession, query: Select[tuple[T]]):
    return (await db.execute(query)).scalar()


async def fetch_all(db: AsyncSession, query: Select[tuple[T]]):
    return (await db.execute(query)).scalars().all()


async def save(db: AsyncSession, instance: object):
    db.add(instance)
    await db.commit()
    await db.refresh(instance)


def make_literal(*values: str) -> Any:
    return Literal[*values]  # type: ignore


def make_union(*types: type) -> Any:
    return Union[*types]  # type: ignore


def get_ip_address(request: Request):
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()  # first IP is the real client
    else:
        if request.client:
            return request.client.host
        else:
            return None


def get_user_agent(request: Request):
    return request.headers.get("user-agent")


def infer_name_from_email(email: str):
    return email.split("@")[0]


def normalize_email(email: str):
    return email.lower()
