from typing import Any
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Uuid, DateTime, func, JSON
import uuid
from datetime import datetime

class Identifiable:
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=lambda: uuid.uuid4()
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