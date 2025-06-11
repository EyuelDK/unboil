import uuid
import secrets
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar
from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload, Mapped
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from unboil_fastapi_auth.models import Models
from unboil_fastapi_auth.utils import fetch_one, normalize_email, save


T = TypeVar("T")
NOT_SET: Any = object()

class Service:
    
    def __init__(self, models: Models):
        self.models = models
        self.crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.session_duration = timedelta(days=14)
        self.session_cookie_name = "access_token"

    def hash_password(self, password: str) -> str:
        return self.crypt_context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.crypt_context.verify(password, hashed_password)

    async def find_user(
        self, 
        db: AsyncSession, 
        email: str = NOT_SET
    ):
        query = select(self.models.User)
        if email is not NOT_SET:
            query = query.where(self.models.User.normalized_email == normalize_email(email))
        return await fetch_one(db=db, query=query)

    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        name: str,
        password: str | None,
    ):
        user = self.models.User(
            email=email,
            name=name,
            hashed_password=self.hash_password(password) if password else None,
        )
        await save(db=db, instance=user)
        return user

    async def create_session(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        ip_address: str | None,
        user_agent: str | None,
    ):
        token = secrets.token_urlsafe(32)
        session = self.models.Session(
            access_token=token,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now() + self.session_duration,
        )
        await save(db=db, instance=session)
        return session

    async def find_session(
        self,
        db: AsyncSession,
        access_token: str = NOT_SET,
        include_user: bool = False,
    ):
        query = select(self.models.Session)
        if access_token is not NOT_SET:
            query = query.where(self.models.Session.access_token == access_token)
        if include_user:
            query = query.options(selectinload(self.models.Session.user))
        return await fetch_one(db=db, query=query)

    def set_access_token_cookie(self, response: Response, access_token: str):
        response.set_cookie(
            key=self.session_cookie_name, value=access_token, httponly=True, secure=True
        )
        
    def get_access_token_cookie(self, request: Request) -> str | None: 
        return request.cookies.get(self.session_cookie_name, None)