import stripe
from aiocache import Cache, cached
from datetime import datetime, timezone
from typing import Any, TypeVar
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import Session
from unboil_fastapi_stripe.config import Config
from unboil_fastapi_stripe.models import Models
from unboil_fastapi_stripe.utils import delete, fetch_all, fetch_one, paginate, save

T = TypeVar("T")
UNSET: Any = object()



class Service:
    
    def __init__(self, models: Models, config: Config):
        self.models = models
        self.config = config
    
    async def ensure_webhook_endpoint(self, url: str):
        endpoint = await self.find_webhook_endpoint(url=url)
        if endpoint is not None:
            return endpoint
        return await stripe.WebhookEndpoint.create_async(
            api_key=self.config.stripe_api_key,
            url=url,
            enabled_events=["*"],
        )

    async def find_webhook_endpoint(self, url: str):
        starting_after = ""
        while True:
            response = await stripe.WebhookEndpoint.list_async(
                api_key=self.config.stripe_api_key,
                limit=100, 
                starting_after=starting_after
            )
            for endpoint in response.data:
                if endpoint.url == url:
                    return endpoint
            if not response.has_more:
                return
            starting_after = response.data[-1].id
    
    
    @cached(ttl=60)
    async def find_price(self, price_id: str):
        return await stripe.Price.retrieve_async(
            api_key=self.config.stripe_api_key,
            id=price_id,
        )
    
    async def find_subscription(
        self,
        db: AsyncSession | Session,
        user_id: Any = UNSET,
        stripe_subscription_item_id: str = UNSET,
        stripe_product_id_in: list[str] = UNSET,
    ):
        query = select(self.models.Subscription)
        if user_id is not UNSET:
            query = query.where(
                self.models.Subscription.customer.has(
                    self.models.Customer.user_id == user_id,
                ),
            )
        if stripe_product_id_in is not UNSET:
            query = query.where(
                self.models.Subscription.stripe_product_id.in_(stripe_product_id_in),
            )
        if stripe_subscription_item_id is not UNSET:
            query = query.where(
                self.models.Subscription.stripe_subscription_item_id == stripe_subscription_item_id,
            )
        return await fetch_one(db=db, query=query)

    async def list_subscriptions(
        self,
        db: AsyncSession | Session,
        offset: int = 0,
        limit: int | None = None,
        user_id: Any = UNSET,
        stripe_subscription_item_ids: list[str] = UNSET,
    ):
        query = select(self.models.Subscription)
        if user_id is not UNSET:
            query = query.where(
                self.models.Subscription.customer.has(
                    self.models.Customer.user_id == user_id
                ),
            )
        if stripe_subscription_item_ids is not UNSET:
            query = query.where(
                self.models.Subscription.stripe_subscription_item_id.in_(stripe_subscription_item_ids),
            )
        return await paginate(db=db, query=query, offset=offset, limit=limit)


    async def create_or_update_subscription(
        self,
        db: AsyncSession,
        stripe_subscription_item_id: str,
        stripe_product_id: str,
        customer_id: uuid.UUID,
        current_period_end: datetime | int,
        auto_commit: bool = True,
    ):
        if isinstance(current_period_end, int):
            current_period_end = datetime.fromtimestamp(current_period_end, tz=timezone.utc)
        subscription = await self.find_subscription(
            db=db,
            stripe_subscription_item_id=stripe_subscription_item_id,
        )
        if subscription is None:
            subscription = self.models.Subscription(
                customer_id=customer_id,
                current_period_end=current_period_end,
                stripe_product_id=stripe_product_id,
                stripe_subscription_item_id=stripe_subscription_item_id,
            )
            await save(db=db, instances=subscription, auto_commit=auto_commit)
        else:
            subscription.customer_id = customer_id
            subscription.current_period_end = current_period_end
            subscription.stripe_product_id = stripe_product_id
            subscription.stripe_subscription_item_id = stripe_subscription_item_id
            await save(db=db, instances=subscription, auto_commit=auto_commit)
        return subscription


    async def create_or_update_subscriptions_from_stripe_subscription(
        self,
        db: AsyncSession,
        stripe_subscription: stripe.Subscription,
    ):
        assert isinstance(stripe_subscription.customer, stripe.Customer)
        customer = await self.find_customer(
            db=db, stripe_customer_id=stripe_subscription.customer.id
        )
        if customer is None:
            return
        async with db.begin():
            return [
                await self.create_or_update_subscription(
                    db=db,
                    auto_commit=False,
                    customer_id=customer.id,
                    stripe_product_id=item.price.product.id,
                    stripe_subscription_item_id=item.id,
                    current_period_end=item.current_period_end,
                )
                for item in stripe_subscription.items.data
                if isinstance(item.price.product, stripe.Product)
            ]

    async def delete_subscriptions_from_stripe_subscription(
        self,
        db: AsyncSession,
        stripe_subscription: stripe.Subscription,
    ):
        subscriptions = self.list_subscriptions(
            db=db,
            stripe_subscription_item_ids=[
                item.id for item in stripe_subscription.items.data
            ]
        )
        await delete(
            db=db,
            instances=subscriptions,
        )

    async def create_customer(
        self, 
        db: AsyncSession | Session,
        user_id: Any,
        name: str | None = None,
        email: str | None = None,
    ):
        stripe_customer = stripe.Customer.create(
            api_key=self.config.stripe_api_key,
            name=name or "",
            email=email or "",
        )
        customer = self.models.Customer(
            user_id=user_id,
            stripe_customer_id=stripe_customer.id,
        )
        await save(db=db, instances=customer)
        return customer


    async def find_customer(
        self, 
        db: AsyncSession | Session, 
        user_id: Any = UNSET,
        stripe_customer_id: str = UNSET,
    ):
        query = select(self.models.Customer)
        if user_id is not UNSET:
            query = query.where(
                self.models.Customer.user_id == user_id,
            )
        if stripe_customer_id is not UNSET:
            query = query.where(
                self.models.Customer.stripe_customer_id == stripe_customer_id
            )
        return await fetch_one(db=db, query=query)

    async def ensure_customer(
        self,
        db: AsyncSession | Session,
        user_id: Any,
        name: str | None = None,
        email: str | None = None,
    ):
        found = await self.find_customer(
            db=db, user_id=user_id
        )
        if found is not None:
            return found
        return await self.create_customer(
            db=db,
            user_id=user_id,
            name=name,
            email=email,
        )


# async def update_subscription_from_stripe(
#     db: AsyncSession,
#     stripe_subscription: stripe.Subscription
# ):
