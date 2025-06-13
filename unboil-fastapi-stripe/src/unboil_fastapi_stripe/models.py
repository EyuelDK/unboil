from typing import Any, Protocol, runtime_checkable
import uuid
from datetime import datetime
from sqlalchemy import (
    UUID,
    TypeDecorator,
    Uuid,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    MetaData,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    DeclarativeBase,
)

__all__ = [
    "Models",
    "UserLike",
    "HasName",
    "HasEmail",
]

class Models:

    def __init__(
        self,
        metadata: MetaData,
        user_foreign_key: str,
    ):

        metadata_ = metadata

        class Base(DeclarativeBase):
            metadata = metadata_

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

        class Customer(Base, Identifiable, Timestamped):
            __tablename__ = "stripe_customers"
            __table_args__ = (
                Index("ix_stripe_customers_stripe_customer_id", "stripe_customer_id"),
                Index("ix_stripe_customers_user_id", "user_id"),
            )
            stripe_customer_id: Mapped[str] = mapped_column(String(255), unique=True)
            user_id: Mapped[Any] = mapped_column(ForeignKey(user_foreign_key), unique=True)
            subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="customer")

            def __init__(self, stripe_customer_id: str, user_id: Any):
                self.stripe_customer_id = stripe_customer_id
                self.user_id = user_id

        class Subscription(Base, Identifiable, Timestamped):
            __tablename__ = "stripe_subscriptions"
            __table_args__ = (
                Index("ix_stripe_subscriptions_stripe_product_id", "stripe_product_id"),
            )
            stripe_subscription_item_id: Mapped[str] = mapped_column(
                String(255), unique=True
            )
            stripe_product_id: Mapped[str] = mapped_column(String(255))
            customer_id: Mapped[uuid.UUID] = mapped_column(
                ForeignKey(f"{Customer.__tablename__}.{Customer.id.key}")
            )
            customer: Mapped["Customer"] = relationship(back_populates="subscriptions")
            current_period_end: Mapped[datetime] = mapped_column(
                DateTime(timezone=True)
            )

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


class UserLike(Protocol):
    id: Mapped[Any]


@runtime_checkable
class HasName(Protocol):
    name: Mapped[str]


@runtime_checkable
class HasEmail(Protocol):
    email: Mapped[str]
