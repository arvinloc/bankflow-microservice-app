import uuid
from dataclasses import dataclass, field

import jwt
from jwt import PyJWKClient

from .config import settings


_jwks_client = PyJWKClient(settings.keycloak_jwks_url, cache_keys=True)


@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    username: str | None = None
    roles: list[str] = field(default_factory=list)
    azp:str |None = None

def decode_token(token: str) -> dict:
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.keycloak_audience,
        issuer=settings.keycloak_issuer,
        options={"require": ["exp", "iss", "sub"]},
    )