import uuid
from collections.abc import AsyncIterator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession

from .security import CurrentUser,decode_token
from .database import SessionLocal
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer()

async def get_db() -> AsyncIterator:
    async with SessionLocal() as session:
        yield session


def get_current_user(
        cred: Annotated[HTTPAuthorizationCredentials,Depends(bearer_scheme)],
) -> CurrentUser:
    try:
        payload = decode_token(cred.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(
        id=uuid.UUID(payload["sub"]),
        username=payload.get("preferred_username"),
        roles=payload.get("realms_access",{}.get("roles",[])),
        azp=payload.get("azp")
    )


DbSession = Annotated[AsyncSession, Depends(get_db)]
UserDep = Annotated[CurrentUser, Depends(get_current_user)]