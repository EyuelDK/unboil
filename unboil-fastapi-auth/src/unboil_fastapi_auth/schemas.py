from typing import Generic, TypeVar
from pydantic import BaseModel

TProvider = TypeVar("TProvider", bound=str)
TParams = TypeVar("TParams", bound=BaseModel)

class SignInRequest(BaseModel, Generic[TProvider, TParams]):
    provider: TProvider
    params: TParams


class SignUpRequest(BaseModel, Generic[TProvider, TParams]):
    provider: TProvider
    params: TParams


class SignInResponse(BaseModel):
    access_token: str
    

class SignUpResponse(BaseModel):
    access_token: str
