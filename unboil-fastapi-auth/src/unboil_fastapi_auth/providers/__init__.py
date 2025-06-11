from typing import TYPE_CHECKING
from pydantic import BaseModel
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

from unboil_fastapi_auth.service import Service
from unboil_fastapi_auth.models import User


class AuthProvider(ABC):

    PROVIDER_NAME: str

    @abstractmethod
    async def signin(
        self, 
        params: BaseModel, 
        db: AsyncSession,
        service: Service
    ) -> User: ...

    @abstractmethod
    async def signup(
        self, 
        params: BaseModel, 
        db: AsyncSession,
        service: Service
    ) -> User: ...
