import hashlib
from typing import IO
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unboil_fastapi_file.file_providers import FileProvider
from unboil_fastapi_file.models import Models
from unboil_fastapi_file.utils import fetch_one, save


class Service:
    
    def __init__(self, models: Models, file_provider: FileProvider):
        self.models = models
        self.file_provider = file_provider
        
    async def upload_file(
        self, 
        db: AsyncSession, 
        key: str, 
        file: IO, 
        content_type: str | None = None
    ):
        found = await self.find_file(db=db, key=key)
        await self.file_provider.upload_object(key=key, file=file)
        file.seek(0)
        content = file.read()
        size = len(content)
        sha256 = hashlib.sha256(content).hexdigest()
        if found is None:
            uploaded = self.models.File(
                key=key,
                size=size,
                sha256=sha256,
                content_type=content_type,
            )
            await save(db=db, instance=uploaded)
            return uploaded
        else:
            found.size = size
            found.sha256 = sha256
            found.content_type = content_type
            await save(db=db, instance=found)
            return found
            
        
    async def find_file(self, db: AsyncSession, key: str):
        query = select(self.models.File)
        query = query.where(self.models.File.key == key)
        return await fetch_one(db=db, query=query)
