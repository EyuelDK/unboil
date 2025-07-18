from typing import Any, AsyncIterable, Callable, Iterable, Sequence
from sqlalchemy import delete, event, select
from sqlalchemy.orm import DeclarativeBase, Session, InstrumentedAttribute, ColumnProperty
from sqlalchemy.ext.asyncio import AsyncSession
from meilisearch import Client
from meilisearch.index import Index
from meilisearch.models.document import Document



def setup_sync[T](
    model: type[T],
    index: Index | tuple[Client, str],
    document_pk: str = "id",
    to_document: Callable[[T], dict[str, Any]] | None = None,
):
    if isinstance(index, tuple):
        client, index_name = index
        index = client.index(index_name)
    
    if to_document is None:
        to_document = _to_document

    @event.listens_for(model, "after_insert")
    def after_insert(mapper, connection, target: T):
        doc = to_document(target)
        index.add_documents([doc])

    @event.listens_for(model, "after_update")
    def after_update(mapper, connection, target: T):
        doc = to_document(target)
        index.add_documents([doc])

    @event.listens_for(model, "after_delete")
    def after_delete(mapper, connection, target: T):
        document_id = getattr(target, document_pk, None)
        if isinstance(document_id, (str, int)):
            index.delete_document(document_id)


async def refresh_sync[T](
    model: type[T],
    id_column: InstrumentedAttribute,
    index: Index | tuple[Client, str],
    session: Session | AsyncSession,
    document_pk: str = "id",
    to_document: Callable[[T], dict[str, Any]] | None = None,
    batch_size: int = 1000,
):
    
    if isinstance(index, tuple):
        client, index_name = index
        index = client.index(index_name)
        
    if to_document is None:
        to_document = _to_document
    
    # sync upserts
    async for batch in _iter_record_batches(model, session, batch_size=batch_size):
        documents = [to_document(record) for record in batch]
        index.add_documents(documents)
    
    # sync deletions
    assert isinstance(id_column.property, ColumnProperty), "Expected id_column to be a ColumnProperty"
    assert len(id_column.property.columns) == 1, "Composite id_column is not supported."
    to_id_column_type = id_column.property.columns[0].type.python_type
    for batch in _iter_document_batches(index, fields=[document_pk], batch_size=batch_size):
        
        # get document ids and transform to db column type
        document_ids = [getattr(document, document_pk) for document in batch]
        batch_ids = [
            to_id_column_type(document_id) for document_id in document_ids
        ]
        
        # get existing ids in batch
        select_statement = select(id_column).where(id_column.in_(batch_ids))
        if isinstance(session, Session):
            existing_ids = session.execute(select_statement).scalars().all()
        else:
            existing_ids = (await session.execute(select_statement)).scalars().all()
        
        # delete missing ids in batch
        missing_ids = set(batch_ids) - set(existing_ids)
        if not missing_ids:
            continue
        delete_statement = delete(model).where(id_column.in_(missing_ids))
        if isinstance(session, Session):
            session.execute(delete_statement)
            session.commit()
        else:
            await session.execute(delete_statement)
            await session.commit()


async def _iter_record_batches[T](
    model: type[T],
    session: Session | AsyncSession,
    batch_size: int = 1000,
) -> AsyncIterable[Sequence[T]]:
    offset = 0
    while True:
        query = select(model).offset(offset).limit(batch_size)
        if isinstance(session, Session):
            records = session.execute(query).scalars().all()
        else:
            records = (await session.execute(query)).scalars().all()
        if not records:
            break
        yield records
        offset += batch_size
        

def _iter_document_batches(
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


def _to_document(instance: Any) -> dict[str, Any]:
    assert isinstance(instance, DeclarativeBase), "Expected instance of DeclarativeBase"
    return {
        c.name: getattr(instance, c.name)
        for c in instance.__table__.columns
    }