from decimal import ROUND_HALF_UP, Decimal
import stripe
import stripe.webhook
from typing import Annotated, Awaitable, Callable
from fastapi import APIRouter, Body, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from unboil_fastapi_stripe.config import Config
from unboil_fastapi_stripe.dependencies import Dependencies
from unboil_fastapi_stripe.models import HasEmail, HasName, UserLike
from unboil_fastapi_stripe.schemas import CheckoutSessionResponse, CheckoutSessionRequest, PriceResponse
from unboil_fastapi_stripe.service import Service

__all__ = ["create_router"]

def create_router(
    config: Config,
    service: Service,
    dependencies: Dependencies,
):
        
    router = APIRouter(prefix="/stripe", tags=["Stripe"])

    @router.get("/prices/{priceId}")
    async def get_price(priceId: str) -> PriceResponse:
        price = await service.find_price(price_id=priceId)
        unit_amount = Decimal(price.unit_amount or 0) / Decimal(100)
        return PriceResponse(
            currency=price.currency,
            unit_amount=unit_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        )

    @router.post("/checkout")
    async def checkout_session(
        request: Annotated[CheckoutSessionRequest, Body()],
        db: Annotated[AsyncSession, Depends(dependencies.get_db)],
        user: Annotated[UserLike, Depends(dependencies.require_user)],
    ) -> CheckoutSessionResponse:
        customer = await service.ensure_customer(
            db=db,
            user_id=user.id,
            name=user.name if isinstance(user, HasName) else None,
            email=user.email if isinstance(user, HasEmail) else None,
        )
        checkout_session = stripe.checkout.Session.create(
            api_key=config.stripe_api_key,
            success_url=request.successUrl,
            cancel_url=request.cancelUrl,
            customer=customer.stripe_customer_id,
            mode=request.type,
            line_items=[
                {
                    "quantity": 1,
                    "price": price_id,
                }
                for price_id in request.priceIds
            ],
        )
        assert checkout_session.url is not None
        return CheckoutSessionResponse(
            checkoutSessionUrl=checkout_session.url
        )


    @router.post("/webhook", include_in_schema=False)
    async def webhook(
        request: Request,
        stripe_signature: Annotated[str, Header(alias="stripe-signature")],
        db: Annotated[AsyncSession, Depends(dependencies.get_db)],
    ):
        payload = await request.body()
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=stripe_signature,
                secret=config.stripe_webhook_secret,
            )
        except (ValueError, stripe.SignatureVerificationError) as e:
            raise HTTPException(status_code=400, detail="Invalid Stripe webhook")

        if event.type == "customer.subscription.created" or \
            event.type == "customer.subscription.updated":
            stripe_subscription = stripe.Subscription(**event.data.object)
            await service.create_or_update_subscriptions_from_stripe_subscription(
                db=db,
                stripe_subscription=stripe_subscription
            )
        elif event.type == "customer.subscription.deleted":
            stripe_subscription = stripe.Subscription(**event.data.object)
            await service.delete_subscriptions_from_stripe_subscription(
                db=db, stripe_subscription=stripe_subscription
            )
            
    return router