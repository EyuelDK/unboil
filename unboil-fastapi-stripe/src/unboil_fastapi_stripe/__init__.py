from typing import Any, Awaitable, Callable, Literal, Protocol, Type, TypedDict
from fastapi import FastAPI
from sqlalchemy import MetaData
from sqlalchemy.orm import Mapped, sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unboil_fastapi_stripe.config import Config
from unboil_fastapi_stripe.dependencies import Dependencies
from unboil_fastapi_stripe.models import Models, UserLike
from unboil_fastapi_stripe.routes import create_router
from unboil_fastapi_stripe.service import Service

class UserModel(Protocol):
    __tablename__: str
    id: Mapped[Any]

class Stripe:
    
    def __init__(
        self, 
        metadata: MetaData, 
        session_maker: async_sessionmaker[AsyncSession] | sessionmaker[Session], 
        stripe_api_key: str,
        stripe_webhook_secret: str,
        user_model: Type[UserModel],
        require_user: Callable[..., UserLike] | Callable[..., Awaitable[UserLike]]
    ):
        self.config = Config(
            stripe_webhook_secret=stripe_webhook_secret
        )
        self.models = Models(
            metadata=metadata,
            user_foreign_key=f"{user_model.__tablename__}.{user_model.id.key}",
        )
        self.service = Service(
            models=self.models, 
            stripe_api_key=stripe_api_key
        )
        self.dependencies = Dependencies(
            service=self.service,
            require_user=require_user,
            session_maker=session_maker,
        )
        
    async def on_startup(self, app: FastAPI):
        router = create_router(
            config=self.config,
            service=self.service,
            dependencies=self.dependencies,
        )
        app.include_router(router, prefix="/api")