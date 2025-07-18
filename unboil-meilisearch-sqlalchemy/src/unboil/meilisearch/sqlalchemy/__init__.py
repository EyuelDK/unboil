from dataclasses import dataclass
from typing import Any, AsyncIterable, Callable, Generic, Iterable, Sequence, TypeVar, cast
from sqlalchemy import delete, event, or_, select, Table, Column
from sqlalchemy.orm import DeclarativeBase, Session, InstrumentedAttribute, ColumnProperty, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from meilisearch import Client
from meilisearch.index import Index
from meilisearch.models.document import Document


__all__ = [
    "MeiliSearchSync",
    "MeiliSearchSyncConfig",
    "setup_sync_listeners",
    "sync_now",
]

T = TypeVar("T")
TDeclarativeBase = TypeVar("TDeclarativeBase", bound=DeclarativeBase)

class MeiliSearchSync(Generic[TDeclarativeBase, T]):
    
    def __init__(self, configs: list["MeiliSearchSyncConfig"]):
        self.configs = configs

    def setup_listeners(self):
        for config in self.configs:
            setup_sync_listeners(
                model=config.model,
                index=config.index,
                to_document=config.to_document,
                primary_key=config.primary_key,
            )
        
    async def sync_now(
        self,
        session: Session | AsyncSession,
        min_version: T | None,
        batch_size: int = 1000,
    ):
        for config in self.configs:
            await sync_now(
                model=config.model,
                id_attribute=config.id_attribute,
                min_version=min_version,
                index=config.index,
                session=session,
                to_document=config.to_document,
                version_column=config.version_column,
                primary_key=config.primary_key,
                batch_size=batch_size,
            )

class MeiliSearchSyncConfig(Generic[TDeclarativeBase, T]):
    
    def __init__(
        self,
        model: type[TDeclarativeBase],
        id_attribute: InstrumentedAttribute,
        index: Index | tuple[Client, str],
        primary_key: str = "id",
        version_column: InstrumentedAttribute[T] | None = None,
        to_document: Callable[[TDeclarativeBase], dict[str, Any]] | None = None,
    ):
        self.model = model
        self.id_attribute = id_attribute
        self.primary_key = primary_key
        self.version_column = version_column
        self.to_document = to_document or _to_document
        if isinstance(index, Index):
            self.index = index
        else:
            client, index_name = index
            self.index = client.index(index_name)
        
        
def setup_sync_listeners[T](
    model: type[T],
    index: Index | tuple[Client, str],
    to_document: Callable[[T], dict[str, Any]],
    primary_key: str = "id",
):
    if isinstance(index, tuple):
        client, index_name = index
        index = client.index(index_name)

    @event.listens_for(model, "after_insert")
    @event.listens_for(model, "after_update")
    def after_update(mapper, connection, target: T):
        doc = to_document(target)
        index.add_documents([doc])

    @event.listens_for(model, "after_delete")
    def after_delete(mapper, connection, target: T):
        document_id = getattr(target, primary_key, None)
        if isinstance(document_id, (str, int)):
            index.delete_document(document_id)


async def sync_now(
    model: type[TDeclarativeBase],
    id_attribute: InstrumentedAttribute,
    min_version: T,
    index: Index | tuple[Client, str],
    session: Session | AsyncSession,
    to_document: Callable[[TDeclarativeBase], dict[str, Any]],
    version_column: InstrumentedAttribute[T] | None = None,
    primary_key: str = "id",
    batch_size: int = 1000,
):
    
    if isinstance(index, tuple):
        client, index_name = index
        index = client.index(index_name)
    
    # sync upserts
    async for batch in _iter_record_pages(
        model=model,
        session=session,
        version_column=version_column, 
        min_version=min_version, 
        page_size=batch_size,
    ):
        documents = [to_document(record) for record in batch]
        index.add_documents(documents)
    
    # sync deletions
    column_property = id_attribute.property
    assert isinstance(column_property, ColumnProperty), "Expected id_column to be a ColumnProperty"
    assert len(column_property.columns) == 1, "Expected id_column to have exactly one column. Composite columns not supported."
    id_column_type = column_property.columns[0].type.python_type
    for batch in _iter_document_pages(index, fields=[primary_key], batch_size=batch_size):
        
        # get document ids and transform to db column type
        document_ids = [getattr(document, primary_key) for document in batch]
        check_ids = [
            id_column_type(document_id) for document_id in document_ids
        ]
        
        # get existing ids in batch
        select_statement = select(id_attribute).where(id_attribute.in_(check_ids))
        if isinstance(session, Session):
            existing_ids = session.execute(select_statement).scalars().all()
        else:
            existing_ids = (await session.execute(select_statement)).scalars().all()
        
        # delete missing ids in batch
        missing_ids = set(check_ids) - set(existing_ids)
        if not missing_ids:
            continue
        delete_statement = delete(id_attribute).where(id_attribute.in_(missing_ids))
        if isinstance(session, Session):
            session.execute(delete_statement)
            session.commit()
        else:
            await session.execute(delete_statement)
            await session.commit()


def _to_document(instance: DeclarativeBase):
    return {
        column.key: getattr(instance, column.key)
        for column in instance.__table__.columns
    }


async def _iter_record_pages(
    model: type[TDeclarativeBase],
    version_column: InstrumentedAttribute[T] | None,
    min_version: T,
    session: Session | AsyncSession,
    page_size: int = 1000,
) -> AsyncIterable[list[TDeclarativeBase]]:
    offset = 0
    while True:
        query = select(model)
        if version_column is not None and min_version is not None:
            query = query.where(version_column > min_version)
        query = query.offset(offset).limit(page_size)
        if isinstance(session, Session):
            records = session.execute(query).scalars().all()
        else:
            records = (await session.execute(query)).scalars().all()
        if not records:
            break
        offset += page_size
        yield list(records)
        

def _iter_document_pages(
    index: Index,
    fields: list[str],
    batch_size: int = 1000,
) -> Iterable[list[Document]]:
    offset = 0
    while True:
        result = index.get_documents({
            "fields": fields,
            "offset": offset,
            "limit": batch_size,
        })
        yield result.results
        offset += batch_size
        if offset >= result.total:
            break