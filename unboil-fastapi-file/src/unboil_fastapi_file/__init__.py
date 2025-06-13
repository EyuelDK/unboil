from dataclasses import dataclass
from typing import Awaitable, Callable
from fastapi import FastAPI, UploadFile
from sqlalchemy import MetaData
from unboil_fastapi_file.dependencies import Dependencies
from unboil_fastapi_file.events import Events
from unboil_fastapi_file.models import Models
from unboil_fastapi_file.routes import create_router
from unboil_fastapi_file.file_providers import FileProvider
from unboil_fastapi_file.service import Service
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

@dataclass(kw_only=True)
class UploadConfig:
    purpose: str
    max_size: int | None = None
    allowed_suffixes: list[str] | None = None
    allowed_content_types: list[str] | None = None

class File:

    def __init__(
        self, 
        metadata: MetaData,
        session_maker: async_sessionmaker[AsyncSession],
        storage_provider: FileProvider, 
        upload_configs: list[UploadConfig]
    ):
        self.storage_provider = storage_provider
        self.upload_configs = upload_configs
        self.events = Events()
        self.models = Models(
            metadata=metadata
        )
        self.service = Service(
            models=self.models,
            file_provider=storage_provider
        )
        self.dependencies = Dependencies(
            session_maker=session_maker
        )

    async def on_startup(self, app: FastAPI):
        router = create_router(
            service=self.service,
            dependencies=self.dependencies,
            events=self.events,
            upload_configs=self.upload_configs
        )
        app.include_router(router)
