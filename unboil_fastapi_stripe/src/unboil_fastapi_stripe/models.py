from typing import Any, Protocol, runtime_checkable
import uuid
from datetime import datetime
from sqlalchemy import UUID, DateTime, ForeignKey, String, func, MetaData
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

__all__ = ["Models", "UserLike", "HasName", "HasEmail"]

@runtime_checkable
class UserLike(Protocol):
    __tablename__: str
    id: Mapped[Any]

@runtime_checkable
class HasName(Protocol):
    name: Mapped[str]

@runtime_checkable
class HasEmail(Protocol):
    email: Mapped[str]

class Models[TUserLike: UserLike]:
    
    def __init__(
        self, 
        metadata: MetaData, 
        user_model: type[TUserLike],
    ):
        
        metadata_ = metadata
        class Base(DeclarativeBase):
            metadata = metadata_
        
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

        class Customer(Base, Identifiable, Timestamped):
            __tablename__ = "stripe_customers"
            stripe_customer_id: Mapped[str] = mapped_column(String, unique=True)
            user_id: Mapped[Any] = mapped_column(
                ForeignKey(f"{user_model.__tablename__}.{user_model.id.key}"), unique=True
            )
            user: Mapped[TUserLike] = relationship()
            subscriptions: Mapped[list["Subscription"]] = relationship()
            
            def __init__(self, user_id: Any, stripe_customer_id: str):
                self.user_id = user_id
                self.stripe_customer_id = stripe_customer_id
                
        class Subscription(Base, Identifiable, Timestamped):
            __tablename__ = "stripe_subscriptions"
            stripe_subscription_item_id: Mapped[str] = mapped_column(String, unique=True)
            stripe_product_id: Mapped[str] = mapped_column(String)
            customer_id: Mapped[uuid.UUID] = mapped_column(
                ForeignKey(f"{Customer.__tablename__}.{Customer.id.key}")
            )
            customer: Mapped["Customer"] = relationship()
            current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
            
            def __init__(
                self, 
                customer_id: uuid.UUID,
                current_period_end: datetime,
                stripe_product_id: str,
                stripe_subscription_item_id: str, 
            ):
                self.customer_id = customer_id
                self.current_period_end = current_period_end
                self.stripe_product_id = stripe_product_id
                self.stripe_subscription_item_id = stripe_subscription_item_id

        self.Customer = Customer
        self.Subscription = Subscription
