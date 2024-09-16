from typing import Annotated

import requests
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from backend.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    if settings.AUTH_SECRET_KEY is None or settings.AUTH_SECRET_KEY == "":
        return "cognita"

    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {token}"},
    )

    return user_info.json()["email"]
