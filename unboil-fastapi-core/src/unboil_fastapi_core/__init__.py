from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from unboil_fastapi_core.dependencies import Dependencies
from unboil_fastapi_core.events import Events
from unboil_fastapi_core.models import Models
from unboil_fastapi_core.settings import Settings

class Core:
    
    def __init__(self, database_url: str | None = None):
        if database_url is None:
            settings = Settings() # type: ignore
            database_url = settings.database_url
        engine = create_async_engine(database_url, echo=False)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        self.events = Events()
        self.models = Models()
        self.dependencies = Dependencies(session_maker)
        
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        await self.events.on_startup.ainvoke(app)
        yield
        await self.events.on_shutdown.ainvoke(app)