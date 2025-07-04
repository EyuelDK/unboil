from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from unboil.fastapi.core.config import Config
from unboil.fastapi.core.dependencies import Dependencies
from unboil.fastapi.core.events import Events
from unboil.fastapi.core.models import Models

class Core:
    
    def __init__(self, database_url: str):
        self.config = Config(database_url=database_url)
        self.events = Events()
        self.models = Models()
        self.dependencies = Dependencies(self.config)
        
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        await self.events.on_startup.ainvoke(app)
        yield
        await self.events.on_shutdown.ainvoke(app)