from datetime import datetime
from typing import Callable, Generic, Literal, TypeVar
from pydantic import BaseModel

from unboil_fastapi_stripe.utils import PaginatedResult

T = TypeVar("T")
R = TypeVar("R")

class CheckoutSessionRequest(BaseModel):
    type: Literal["subscription", "payment"]
    priceIds: list[str]
    successUrl: str
    cancelUrl: str


class CheckoutSessionResponse(BaseModel):
    checkoutSessionUrl: str


class PriceResponse(BaseModel):
    amount: float
    currency: str


class PaginatedResponse(BaseModel, Generic[R]):
    hasMore: bool
    total: int
    offset: int
    limit: int | None
    items: list[R]

    @classmethod
    def from_result(cls, result: PaginatedResult[T], transform: Callable[[T], R]):
        return PaginatedResponse(
            hasMore=result.has_more,
            total=result.total,
            offset=result.offset,
            limit=result.limit,
            items=[transform(item) for item in result.items],
        )


class Subscription(BaseModel):
    stripeProductId: str
    currentPeriodEnd: datetime
