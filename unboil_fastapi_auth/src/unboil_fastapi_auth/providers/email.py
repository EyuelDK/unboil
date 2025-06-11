from typing import TYPE_CHECKING
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from unboil_fastapi_auth.service import Service
from unboil_fastapi_auth.models import User
from unboil_fastapi_auth.providers import AuthProvider
from unboil_fastapi_auth.utils import infer_name_from_email


class EmailAuthProvider(AuthProvider):

    PROVIDER_NAME = "email"

    async def signin(
        self, 
        params: "SignInWithEmailParams", 
        db: AsyncSession,
        service: Service
    ) -> User:
        found = await service.find_user(db=db, email=params.email)
        if found is None or found.hashed_password is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        verified = service.verify_password(
            password=params.password, hashed_password=found.hashed_password
        )
        if not verified:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return found

    async def signup(
        self, 
        params: "SignUpWithEmailParams", 
        db: AsyncSession,
        service: Service,
    ) -> User:
        found = await service.find_user(db=db, email=params.email)
        if found is not None:
            raise HTTPException(status_code=400, detail="User already exists")
        created = await service.create_user(
            db=db,
            email=params.email,
            name=(
                infer_name_from_email(email=params.email)
                if params.name is None
                else params.name
            ),
            password=params.password,
        )
        return created


class SignInWithEmailParams(BaseModel):
    email: str
    password: str


class SignUpWithEmailParams(BaseModel):
    name: str | None
    email: str
    password: str
