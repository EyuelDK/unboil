from datetime import datetime, timezone
from typing import Awaitable, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from unboil_fastapi_stripe.models import UserLike
from unboil_fastapi_stripe.service import Service
from unboil_fastapi_stripe.utils import InferDepends

class Dependencies:

    def __init__(
        self,
        service: Service,
        session_maker: async_sessionmaker[AsyncSession],
        require_user: Callable[..., UserLike] | Callable[..., Awaitable[UserLike]],
    ):
        self.service = service
        self.session_maker = session_maker
        self.require_user = require_user

    async def get_db(self):
        async with self.session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    def get_subscription(self, product_ids: list[str]):
        async def dependency(
            user = InferDepends(self.require_user),
            db = InferDepends(self.get_db),
        ):
            subscription = await self.service.find_subscription(
                db=db,
                user_id=user.id,
                stripe_product_id_in=product_ids,
            )
            return subscription
        return dependency

    async def requires_subscription(self, allowed_product_ids: list[str]):
        def dependency(
            subscription = InferDepends(self.get_subscription(allowed_product_ids)),
        ):
            if subscription is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED"
                )
            if subscription.current_period_end < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED"
                )
            return subscription
        return dependency
