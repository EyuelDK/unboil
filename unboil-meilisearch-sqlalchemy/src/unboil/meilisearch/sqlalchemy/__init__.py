from typing import Any, Callable, TypeVar, cast
from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase
from meilisearch import Client


T = TypeVar("T")

def auto_sync(
    model: type[T],
    client: Client,
    primary_key: str = "id",
    index_name: str | None = None,
    to_document: Callable[[T], dict[str, Any]] | None = None,
):
    if index_name is None:
        index_name = cast(DeclarativeBase, model).__tablename__
        
    assert index_name, (
        "Unable to determine index name. "
        "Provide an index_name or ensure the model has a __tablename__."
    )

    if to_document is None:
        to_document = _to_document

    index = client.index(index_name)

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
        document_id = getattr(target, primary_key, None)
        if document_id is not None:
            assert isinstance(document_id, (str, int)), (
                f"Primary key '{primary_key}' must be of type str or int, "
                f"got {type(document_id).__name__}."
            )
            index.delete_document(document_id)
            

def _to_document(instance: Any) -> dict[str, Any]:
    assert isinstance(instance, DeclarativeBase), "Expected instance of DeclarativeBase"
    return {
        c.name: getattr(instance, c.name)
        for c in instance.__table__.columns
    }