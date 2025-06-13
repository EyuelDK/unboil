import uuid

from pydantic import BaseModel


class UploadResponse(BaseModel):
    id: uuid.UUID