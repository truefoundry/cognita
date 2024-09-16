from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.server.auth.config import oauth
from backend.settings import settings

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    # absolute url for callback
    # we will define it below
    redirect_uri = settings.QA_BACKEND_HOSTED_URL + "/v1/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f"<h1>{error.error}</h1>")
    data = {
        "access_token": token["access_token"],
        "user": token["userinfo"]["email"],
    }
    redirect_url = f"{settings.QA_FRONTEND_URL}/callback?"
    query_params = "&".join([f"{key}={value}" for key, value in data.items()])
    redirect_url += query_params
    return RedirectResponse(url=redirect_url)


@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return True
