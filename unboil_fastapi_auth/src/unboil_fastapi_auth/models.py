from typing import TYPE_CHECKING, Protocol, TypeVar
import uuid
from datetime import datetime
from sqlalchemy import (
    UUID,
    Boolean,
    ForeignKey,
    MetaData,
    String,
    Unicode,
    DateTime,
    func,
    Index,
    event,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    DeclarativeBase,
    relationship,
    declared_attr,
    declarative_base,
)

from unboil_fastapi_auth.utils import normalize_email

__all__ = ["Models"]

class Models:
    
    def __init__(self, metadata: MetaData):
        
        Base = declarative_base(metadata=metadata)
        
        self.User = type("User", (Base, User), {})
        self.Session = type("Session", (Base, Session), {})
        
        @event.listens_for(self.User, "before_insert")
        @event.listens_for(self.User, "before_update")
        def normalize_email(mapper, connection, target: User):
            target.normalized_email = normalize_email(target.email)

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

class User(Identifiable, Timestamped):
    __tablename__ = "auth_users"
    __table_args__ = (Index("ix_user_normalized_email", "normalized_email"),)
    email: Mapped[str] = mapped_column(Unicode, unique=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    name: Mapped[str] = mapped_column(Unicode)
    normalized_email: Mapped[str] = mapped_column(Unicode, unique=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    
    @declared_attr
    def sessions(cls) -> Mapped[list["Session"]]:
        return relationship(back_populates="user")

    def __init__(
        self,
        email: str,
        name: str,
        hashed_password: str | None,
        is_email_verified: bool = False,
    ):
        self.email = email
        self.is_email_verified = is_email_verified
        self.name = name
        self.normalized_email = normalize_email(email)
        self.hashed_password = hashed_password
    
class Session(Identifiable, Timestamped):
    __tablename__ = "auth_sessions"
    __table_args__ = (Index("ix_session_access_token", "access_token"),)
    access_token: Mapped[str] = mapped_column(String)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    @declared_attr
    def user_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(ForeignKey("auth_users.id"))
    
    @declared_attr
    def user(cls) -> Mapped["User"]:
        return relationship(back_populates="sessions")

    def __init__(
        self,
        access_token: str,
        user_id: uuid.UUID,
        ip_address: str | None,
        user_agent: str | None,
        expires_at: datetime,
    ):
        self.access_token = access_token
        self.user_id = user_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.expires_at = expires_at
