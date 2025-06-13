from pathlib import Path
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Any, Literal, NewType, Type, Union
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from unboil_fastapi_file import UploadConfig
from unboil_fastapi_file.dependencies import Dependencies
from unboil_fastapi_file.events import AfterFileUploadContext, BeforeFileUploadContext, Events
from unboil_fastapi_file.file_providers import FileProvider
from unboil_fastapi_file.schemas import UploadResponse
from unboil_fastapi_file.service import Service
from unboil_fastapi_file.utils import make_literal


def create_router(
    service: Service,
    dependencies: Dependencies,
    events: Events,
    upload_configs: list[UploadConfig],
):
    purpose_mappings = {config.purpose: config for config in upload_configs}

    router = APIRouter(prefix="/file", tags=["File"])

    async def upload_file(
        purpose: str, 
        file: Annotated[UploadFile, File()],
        db: Annotated[AsyncSession, Depends(dependencies.get_db)]
    ) -> UploadResponse:
        
        await events.before_upload.ainvoke(
            BeforeFileUploadContext(purpose=purpose, upload=file)
        )

        purpose_config = purpose_mappings[purpose]

        if purpose_config.allowed_suffixes:
            suffix = Path(file.filename or "").suffix
            if suffix not in purpose_config.allowed_suffixes:
                raise HTTPException(status_code=400, detail="Invalid file extension")

        if purpose_config.allowed_content_types:
            if file.content_type not in purpose_config.allowed_content_types:
                raise HTTPException(status_code=400, detail="Invalid file content type")
         
        size = len(await file.read())
        if purpose_config.max_size:
            if size > purpose_config.max_size:
                raise HTTPException(status_code=400, detail="File too large")
        
        key = f"uploads/{uuid.uuid4()}/{file.filename}"
        uploaded = await service.upload_file(
            db=db,
            key=key,
            file=file.file,
            content_type=file.content_type
        )
        
        await events.after_upload.ainvoke(
            AfterFileUploadContext(purpose=purpose, info=uploaded, upload=file)
        )
        
        return UploadResponse(id=uploaded.id)

    upload_file.__annotations__["purpose"] = make_literal(
        *[pc.purpose for pc in upload_configs]
    )

    router.post("/files/{purpose}/upload")(upload_file)

    @router.get("/files/{file_id}/download")
    async def download_file(file_id: str):
        return {"file_id": file_id}

    return router
