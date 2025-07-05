from contextlib import asynccontextmanager
from fastapi import FastAPI

from .config import Config
from .dependencies import Dependencies
from .events import Events
from .models import Models
from .services import Services

class Core:
    
    def __init__(self, database_url: str):
        self.config = Config(database_url=database_url)
        self.events = Events()
        self.models = Models()
        self.services = Services(self.config)
        self.dependencies = Dependencies(self.services)
        
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        await self.events.on_startup.ainvoke(app)
        yield
        await self.events.on_shutdown.ainvoke(app)