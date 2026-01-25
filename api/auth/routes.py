from typing import Any, Dict
from http.cookiejar import Cookie

import httpx
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse

from api.settings import settings

SESSION_COOKIE_NAME = "session_token"

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(payload: Dict[str, Any] = Body(..., description="Identifiants Directus (email, password)")):
    """Proxy Directus /auth/login en conservant les cookies (session)."""
    try:
        async with httpx.AsyncClient(base_url=settings.DIRECTUS_URL, timeout=10) as client:
            response = await client.post(
                "/auth/login",
                json=payload,
                headers={"Accept": "application/json"},
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Directus indisponible: {exc}") from exc

    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = {"detail": response.text}
        raise HTTPException(status_code=response.status_code, detail=detail)

    fastapi_response = JSONResponse(
        content=response.json(),
        status_code=response.status_code,
    )

    for cookie in response.cookies.jar:
        _set_cookie_from_directus(fastapi_response, cookie)

    return fastapi_response


def _set_cookie_from_directus(response: JSONResponse, cookie: Cookie) -> None:
    rest = getattr(cookie, "rest", getattr(cookie, "_rest", {})) or {}
    samesite = rest.get("SameSite") or rest.get("samesite")
    httponly = bool(rest.get("HttpOnly") or rest.get("httponly"))

    cookie_name = SESSION_COOKIE_NAME if cookie.name.startswith("directus") else cookie.name

    response.set_cookie(
        key=cookie_name,
        value=cookie.value,
        max_age=cookie.expires,
        expires=cookie.expires,
        path=cookie.path or "/",
        domain=cookie.domain,
        secure=cookie.secure,
        httponly=httponly,
        samesite=samesite.lower() if isinstance(samesite, str) else None,
    )
