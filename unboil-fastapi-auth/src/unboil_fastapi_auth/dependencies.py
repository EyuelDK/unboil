from typing import TYPE_CHECKING, Annotated, Generic, NewType, TypeVar
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from fastapi import status

from unboil_fastapi_auth.models import Models, User
from unboil_fastapi_auth.service import Service


class Dependencies:
        
    def __init__(
        self, 
        service: Service, 
        session_maker: async_sessionmaker[AsyncSession]
    ):
        self.service = service
        self.session_maker = session_maker
        

    async def get_db(self):
        async with self.session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    def get_access_token(self, request: Request) -> str | None:
        header_value = request.headers.get("Authorization")
        if header_value and header_value.startswith("Bearer "):
            return header_value.split(maxsplit=1)[1]
        return self.service.get_access_token_cookie(request)

    async def get_user(
        self,
        access_token: Annotated[str | None, Depends(get_access_token)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ):
        if access_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED"
            )
        session = await self.service.find_session(
            db=db, access_token=access_token, include_user=True
        )
        return None if session is None else session.user

    async def require_user(
        self, 
        user: Annotated[User | None, Depends(get_user)]
    ):
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED"
            )
        return user
