from typing import Awaitable, Callable
from fastapi import FastAPI
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unboil_fastapi_stripe.dependencies import Dependencies
from unboil_fastapi_stripe.models import Models, UserLike
from unboil_fastapi_stripe.routes import create_router
from unboil_fastapi_stripe.service import Service


class Stripe:
    
    def __init__(
        self, 
        metadata: MetaData, 
        session_maker: async_sessionmaker[AsyncSession], 
        stripe_api_key: str,
        stripe_webhook_secret: str,
        user_model: type[UserLike],
        require_user: Callable[..., UserLike] | Callable[..., Awaitable[UserLike]]
    ):
        self.require_user = require_user
        self.stripe_webhook_secret = stripe_webhook_secret
        self.models = Models(
            metadata=metadata,
            user_model=user_model,
        )
        self.service = Service(
            models=self.models, 
            stripe_api_key=stripe_api_key
        )
        self.dependencies = Dependencies(
            session_maker=session_maker,
        )
        
    async def setup_routes(self, app: FastAPI):
        router = create_router(
            stripe_webhook_secret=self.stripe_webhook_secret,
            service=self.service,
            dependencies=self.dependencies,
            require_user=self.require_user,
        )
        app.include_router(router, prefix="/api")