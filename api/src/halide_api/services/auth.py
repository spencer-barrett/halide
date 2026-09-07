from typing import Annotated
from fastapi import Depends, HTTPException
import jwt
from jwt import PyJWKClient
from halide_api.config import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


jwks_url = (f"https://{settings.auth0_domain}/.well-known/jwks.json")
jwks_client = PyJWKClient(jwks_url)
bearer = HTTPBearer()

def get_current_user(creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]) -> str:
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(creds.credentials)
        payload = jwt.decode(creds.credentials, signing_key.key, algorithms=[settings.auth0_algorithms], audience=settings.auth0_audience, issuer=(f"https://{settings.auth0_domain}/"))
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid token")
    return payload["sub"]

CurrentUser = Annotated[str, Depends(get_current_user)]