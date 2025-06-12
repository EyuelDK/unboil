from datetime import datetime, timezone
from typing import Awaitable, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from unboil_fastapi_stripe.models import Subscription, UserLike
from unboil_fastapi_stripe.service import Service

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
            user: UserLike = Depends(self.require_user),
            db: AsyncSession = Depends(self.get_db),
        ):
            subscription = await self.service.find_subscription(
                db=db,
                user_id=user.id,
                stripe_product_ids=product_ids,
                max_current_period_end=datetime.now(timezone.utc),
            )
            return subscription
        return dependency

    async def requires_subscription(self, product_ids: list[str]):
        def dependency(
            subscription: Subscription | None = Depends(self.get_subscription(product_ids)),
        ):
            if subscription is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED"
                )
            return subscription
        return dependency
