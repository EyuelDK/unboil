from typing import Literal
from pydantic import BaseModel


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