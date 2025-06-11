from fastapi import FastAPI
from sqlalchemy import MetaData
from unboil_fastapi_auth.dependencies import Dependencies
from unboil_fastapi_auth.models import Models
from unboil_fastapi_auth.providers import AuthProvider
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unboil_fastapi_auth.routes import create_router
from unboil_fastapi_auth.service import Service


class Auth:
    
    def __init__(
        self, 
        metadata: MetaData, 
        session_maker: async_sessionmaker[AsyncSession], 
        providers: list[AuthProvider]
    ):
        self.providers = providers
        self.models = Models(metadata=metadata)
        self.service = Service(models=self.models)
        self.dependencies = Dependencies(
            service=self.service,
            session_maker=session_maker
        )
        
    async def setup_routes(self, app: FastAPI):
        router = create_router(
            providers=self.providers,
            service=self.service,
            dependencies=self.dependencies,
        )
        app.include_router(router, prefix="/api")
