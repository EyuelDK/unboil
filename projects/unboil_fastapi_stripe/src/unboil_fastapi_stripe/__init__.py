from typing import Awaitable, Callable
from fastapi import FastAPI
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unboil_fastapi_stripe.dependencies import Dependencies
from unboil_fastapi_stripe.models import Models, UserLikeModel
from unboil_fastapi_stripe.routes import Routes
from unboil_fastapi_stripe.service import Service


class Stripe:
    
    def __init__(
        self, 
        app: FastAPI,
        metadata: MetaData, 
        session_maker: async_sessionmaker[AsyncSession], 
        user_model: type[UserLikeModel],
        require_user: Callable[..., UserLikeModel] | Callable[..., Awaitable[UserLikeModel]]
    ):
        self.models = Models(
            metadata=metadata,
            user_model=user_model,
        )
        self.service = Service(models=self.models)
        self.dependencies = Dependencies(
            session_maker=session_maker,
        )
        self.routes = Routes(
            service=self.service,
            dependencies=self.dependencies,
            require_user=require_user,
        )
        app.include_router(self.routes.router, prefix="/api")
