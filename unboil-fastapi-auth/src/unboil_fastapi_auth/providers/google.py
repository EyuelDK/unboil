from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from unboil_fastapi_auth.service import Service
from unboil_fastapi_auth.providers import AuthProvider
from unboil_fastapi_auth.utils import infer_name_from_email

from unboil_fastapi_auth.models import User


class GoogleAuthProvider(AuthProvider):

    PROVIDER_NAME = "google"

    async def signin(
        self, 
        params: "SignInWithGoogleParams", 
        db: AsyncSession,
        service: Service
    ) -> User:
        if params.token_type == "access_token":
            user_info = get_user_info(params.token)
            email = user_info.email
        else:
            id_info = get_id_info(params.token)
            email = id_info.email
        found = await service.find_user(db=db, email=email)
        if found is None or found.hashed_password is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return found

    async def signup(
        self, 
        params: "SignUpWithGoogleParams", 
        db: AsyncSession,
        service: Service
    ) -> User:
        if params.token_type == "access_token":
            user_info = get_user_info(params.token)
            email = user_info.email
        else:
            id_info = get_id_info(params.token)
            email = id_info.email
        found = await service.find_user(db=db, email=email)
        if found is not None:
            raise HTTPException(status_code=400, detail="User already exists")
        created = await service.create_user(
            db=db,
            email=email,
            name=(
                infer_name_from_email(email=email)
                if params.name is None
                else params.name
            ),
            password=params.password,
        )
        return created


class SignInWithGoogleParams(BaseModel):
    token_type: Literal["access_token", "id_token"]
    token: str
    
class SignUpWithGoogleParams(BaseModel):
    token_type: Literal["access_token", "id_token"]
    token: str
    name: str | None
    password: str | None

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

@dataclass(kw_only=True)
class UserInfo:
    email: str

def get_user_info(access_token: str):
    credentials = Credentials(token=access_token)
    service = build('oauth2', 'v2', credentials=credentials)
    response = service.userinfo().get().execute()
    return UserInfo(
        email=response["email"]
    )
    
import google.oauth2.id_token
from google.auth.transport import requests
    
@dataclass(kw_only=True)
class IdInfo:
    email: str
    
def get_id_info(id_token: str):
    id_info = google.oauth2.id_token.verify_oauth2_token(id_token, requests.Request())
    return IdInfo(
        email=id_info["email"]
    )
