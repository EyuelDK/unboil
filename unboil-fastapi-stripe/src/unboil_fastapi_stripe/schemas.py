from typing import Literal
from pydantic import BaseModel, Field


class CheckoutSessionRequest(BaseModel):
    type: Literal["subscription", "payment"]
    priceIds: list[str]
    successUrl: str
    cancelUrl: str

class CheckoutSessionResponse(BaseModel):
    checkoutSessionUrl: str
