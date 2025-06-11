from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from typing import Annotated, get_type_hints
from sqlalchemy.ext.asyncio import AsyncSession
from unboil_fastapi_auth.dependencies import Dependencies
from unboil_fastapi_auth.service import Service
from unboil_fastapi_auth.utils import get_ip_address, get_user_agent, make_literal, make_union
from unboil_fastapi_auth.providers import AuthProvider
from unboil_fastapi_auth.schemas import (
    SignInRequest,
    SignUpRequest,
    SignInResponse,
    SignUpResponse,
)

__all__ = ["create_router"]

    
def create_router( 
    service: Service,
    providers: list[AuthProvider],
    dependencies: Dependencies,
):

    providers_map: dict[str, AuthProvider] = {
        provider.PROVIDER_NAME: provider for provider in providers
    }

    router = APIRouter(prefix="/auth", tags=["Auth"])

    async def signin(
        body: Annotated[SignInRequest, Body()],
        request: Request,
        response: Response,
        db: Annotated[AsyncSession, Depends(dependencies.get_db)],
    ) -> SignInResponse:
        provider = providers_map.get(body.provider, None)
        if provider is None:
            raise HTTPException(
                status_code=400, detail=f"Provider '{body.provider}' not found."
            )
        user = await provider.signin(params=body.params, db=db, service=service)
        session = await service.create_session(
            db=db,
            user_id=user.id,
            ip_address=get_ip_address(request),
            user_agent=get_user_agent(request),
        )
        service.set_access_token_cookie(
            response=response, access_token=session.access_token
        )
        return SignInResponse(access_token=session.access_token)

    signin.__annotations__["body"] = make_union(
        *(
            SignInRequest[make_literal(provider.PROVIDER_NAME), param_type]
            for provider in providers_map.values()
            if (param_type := get_type_hints(provider.signin).get("params"))
        )
    )

    router.post("/signin")(signin)

    async def signup(
        body: Annotated[SignUpRequest, Body()],
        request: Request,
        response: Response,
        db: Annotated[AsyncSession, Depends(dependencies.get_db)],
    ) -> SignUpResponse:
        assert isinstance(body, SignUpRequest)
        provider = providers_map.get(body.provider, None)
        if provider is None:
            raise HTTPException(
                status_code=400, detail=f"Provider '{body.provider}' not found."
            )
        user = await provider.signup(params=body.params, db=db, service=service)
        session = await service.create_session(
            db=db,
            user_id=user.id,
            ip_address=get_ip_address(request),
            user_agent=get_user_agent(request),
        )
        service.set_access_token_cookie(
            response=response, access_token=session.access_token
        )
        return SignUpResponse(access_token=session.access_token)

    signup.__annotations__["body"] = make_union(
        *(
            SignUpRequest[make_literal(provider.PROVIDER_NAME), param_type]
            for provider in providers_map.values()
            if (param_type := get_type_hints(provider.signup).get("params"))
        )
    )

    router.post("/signup")(signup)
    
    return router