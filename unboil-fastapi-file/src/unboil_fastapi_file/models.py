from datetime import datetime
from typing import Protocol
import uuid
from sqlalchemy import UUID, DateTime, Index, Integer, MetaData, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declarative_base

__all__ = ["Models", "FileInfo"]


class Models:

    def __init__(self, metadata: MetaData):        
        Base = declarative_base(metadata=metadata)
        self.File = type("File", (Base, FileInfo), {})

class Identifiable:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: uuid.uuid4()
    )

class Timestamped:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )

class FileInfo(Identifiable, Timestamped):
    __tablename__ = "file_infos"
    __table_args__ = (
        Index("idx_files_size_sha256", "size", "sha256"),
    )
    key: Mapped[str] = mapped_column(String, unique=True)
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String)
    content_type: Mapped[str | None] = mapped_column(String)

    def __init__(
        self, key: str, size: int, sha256: str, content_type: str | None
    ):
        self.key = key
        self.size = size
        self.sha256 = sha256
        self.content_type = content_type