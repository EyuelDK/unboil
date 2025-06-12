import stripe
import stripe.webhook
from typing import Annotated, Awaitable, Callable
from fastapi import APIRouter, Body, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from unboil_fastapi_stripe import config, service
from unboil_fastapi_stripe.dependencies import Dependencies
from unboil_fastapi_stripe.models import UserFull, UserLikeModel
from unboil_fastapi_stripe.schemas import CheckoutSessionResponse, CheckoutSession
from unboil_fastapi_stripe.service import Service

__all__ = ["Routes"]

class Routes:
    
    def __init__(
        self, 
        service: Service,
        dependencies: Dependencies,
        require_user: Callable[..., UserLikeModel] | Callable[..., Awaitable[UserLikeModel]]
    ):
        
        router = APIRouter(prefix="/stripe", tags=["Stripe"])
        self.router = router

        @router.post("/checkout")
        async def checkout_session(
            request: Annotated[CheckoutSession, Body()],
            db: Annotated[AsyncSession, Depends(dependencies.get_db)],
            user: Annotated[UserLikeModel, Depends(require_user)],
        ):
            
            name = None
            email = None
            if isinstance(user, UserFull):
                name = user.name
                email = user.email
            customer = await service.ensure_customer(
                db=db,
                user_id=user.id,
                name=name,
                email=email,
            )
            checkout_session = stripe.checkout.Session.create(
                success_url=request.success_url,
                cancel_url=request.cancel_url,
                customer=customer.stripe_customer_id,
                mode=request.type,
                line_items=[
                    {
                        "quantity": 1,
                        "price": price_id,
                    }
                    for price_id in request.price_ids
                ],
            )
            assert checkout_session.url is not None
            return CheckoutSessionResponse(checkout_session_url=checkout_session.url)


        @router.post("/webhook")
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

            if event.type == "customer.subscription.created":
                stripe_subscription = stripe.Subscription(**event.data.object)
                assert isinstance(stripe_subscription.customer, stripe.Customer)
                customer = await service.find_customer(
                    db=db, stripe_customer_id=stripe_subscription.customer.id
                )
                if customer is None:
                    raise HTTPException(status_code=404, detail="Customer not found")
                await service.create_subscriptions_from_stripe_subscription(
                    db=db,
                    customer_id=customer.id,
                    stripe_subscription=stripe_subscription
                )
            elif event.type == "customer.subscription.updated":
                stripe_subscription = stripe.Subscription(**event.data.object)
                await service.update_subscriptions_from_stripe_subscription(
                    db=db, stripe_subscription=stripe_subscription
                )
            elif event.type == "customer.subscription.deleted":
                stripe_subscription = stripe.Subscription(**event.data.object)
                await service.delete_subscriptions_from_stripe_subscription(
                    db=db, stripe_subscription=stripe_subscription
                )