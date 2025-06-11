from typing import Literal
from pydantic import BaseModel


class CheckoutSession(BaseModel):
    type: Literal["subscription", "payment"]
    price_ids: list[str]
    success_url: str
    cancel_url: str

class CheckoutSessionResponse(BaseModel):
    checkout_session_url: str