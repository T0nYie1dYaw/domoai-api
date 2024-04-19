from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from app.settings import Settings, get_settings

security = HTTPBearer(scheme_name="DomoAI")


async def api_auth(
        token: HTTPAuthorizationCredentials = Depends(security),
        settings: Settings = Depends(get_settings)
):
    if settings.api_auth_token and token.credentials != settings.api_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
