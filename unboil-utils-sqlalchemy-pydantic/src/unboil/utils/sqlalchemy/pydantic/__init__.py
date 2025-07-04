from typing import Any

from pydantic import TypeAdapter
from sqlalchemy import JSON, Dialect, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB


class PydanticTypeDecorator(TypeDecorator):
    cache_ok = True  # Performance hint

    def __init__(self, pydantic_type: type[Any]):
        super().__init__()
        self.pydantic_type = pydantic_type
        self.adapter = TypeAdapter(pydantic_type)

    def load_dialect_impl(self, dialect: Dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect: Dialect):
        if isinstance(value, self.pydantic_type):
            return self.adapter.dump_python(value)
        return value

    def process_result_value(self, value: Any, dialect: Dialect):
        if value is None:
            return None
        return self.adapter.validate_python(value)
    

    def __repr__(self) -> str:
        # Used by alembic
        return repr(self.impl)