from typing import Any, Callable, TypeVar, cast
from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase
from meilisearch import Client


T = TypeVar("T")

def sync(
    model: type[T],
    meili_client: Client,
    primary_key: str = "id",
    index_name: str | None = None,
    to_dict: Callable[[T], dict[str, Any]] | None = None,
):
    if index_name is None:
        index_name = cast(DeclarativeBase, model).__tablename__
        
    assert index_name, (
        "Unable to determine index name. "
        "Provide an index_name or ensure the model has a __tablename__."
    )

    if to_dict is None:
        to_dict = _to_dict

    index = meili_client.index(index_name)

    @event.listens_for(model, "after_insert")
    def after_insert(mapper, connection, target: T):
        doc = to_dict(target)
        index.add_documents([doc])

    @event.listens_for(model, "after_update")
    def after_update(mapper, connection, target: T):
        doc = to_dict(target)
        index.add_documents([doc])

    @event.listens_for(model, "after_delete")
    def after_delete(mapper, connection, target: T):
        pk = getattr(target, primary_key, None)
        if pk is not None:
            index.delete_document(str(pk))
            

def _to_dict(instance: Any) -> dict[str, Any]:
    assert isinstance(instance, DeclarativeBase), "Expected instance of DeclarativeBase"
    return {
        c.name: getattr(instance, c.name)
        for c in instance.__table__.columns
    }