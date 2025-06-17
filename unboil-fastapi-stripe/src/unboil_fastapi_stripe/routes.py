import stripe
from fastapi import APIRouter, HTTPException, Header, Request
from unboil_fastapi_stripe.config import Config
from unboil_fastapi_stripe.events import Events

__all__ = ["create_router"]


def create_router(
    events: Events,
    config: Config,
):

    router = APIRouter(prefix="/stripe", tags=["Stripe"])

    @router.post("/webhook", include_in_schema=False)
    async def webhook(
        request: Request,
        stripe_signature: str = Header(alias="stripe-signature"),
    ):
        payload = await request.body()
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=stripe_signature,
                secret=config.stripe_webhook_secret,
            )
        except (ValueError, stripe.SignatureVerificationError):
            raise HTTPException(status_code=400, detail="Invalid Stripe webhook")

        if events.on_event_received.has_listener():
            await events.on_event_received.ainvokable(request)(event)

        if event.type == "customer.subscription.created":
            if events.on_subscription_created.has_listener():
                subscription = stripe.Subscription.construct_from(
                    event.data.object, config.stripe_api_key
                )
                await events.on_subscription_created.ainvokable(request)(subscription)

        elif event.type == "customer.subscription.updated":
            if events.on_subscription_updated.has_listener():
                subscription = stripe.Subscription.construct_from(
                    event.data.object, config.stripe_api_key
                )
                await events.on_subscription_updated.ainvokable(request)(subscription)
        
        elif event.type == "customer.subscription.deleted":
            if events.on_subscription_deleted.has_listener():
                subscription = stripe.Subscription.construct_from(
                    event.data.object, config.stripe_api_key
                )
                await events.on_subscription_deleted.ainvokable(request)(subscription)
                
    return router