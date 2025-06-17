from dataclasses import dataclass


@dataclass(kw_only=True)
class Config:
    stripe_api_key: str
    stripe_webhook_secret: str