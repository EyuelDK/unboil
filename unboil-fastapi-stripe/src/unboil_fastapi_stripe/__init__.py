from fastapi import FastAPI

from unboil_fastapi_stripe.config import Config
from unboil_fastapi_stripe.events import Events
from unboil_fastapi_stripe.routes import create_router


class Stripe:
    
    def __init__(
        self,
        stripe_api_key: str,
        stripe_webhook_secret: str,
    ):
        self.events = Events()
        self.config = Config(
            stripe_api_key=stripe_api_key,
            stripe_webhook_secret=stripe_webhook_secret,
        )
        self.router = create_router(
            events=self.events,
            config=self.config,
        )