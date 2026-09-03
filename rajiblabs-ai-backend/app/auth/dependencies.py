"""JWT creation/verification and RequireAdmin (dual-email single identity)."""
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import get_settings
from app.database import get_db

bearer_scheme = HTTPBearer(auto_error=False)
LOGIN_ATTEMPTS: dict[str, list[float]] = {}


def check_login_rate_limit(ip: str, limit: int = 5, window: int = 60) -> None:
    now = time.time()
    attempts = [t for t in LOGIN_ATTEMPTS.get(ip, []) if now - t < window]
    if len(attempts) >= limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many login attempts, try again later.")
    attempts.append(now)
    LOGIN_ATTEMPTS[ip] = attempts


def create_access_token(email: str) -> str:
    s = get_settings()
    payload = {"sub": email.lower(), "iss": s.jwt_issuer, "type": "access",
               "exp": int(time.time()) + s.jwt_expire_minutes * 60}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def create_refresh_token(email: str) -> str:
    s = get_settings()
    payload = {"sub": email.lower(), "iss": s.jwt_issuer, "type": "refresh",
               "exp": int(time.time()) + s.refresh_expire_days * 86400}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def decode_token(token: str, expected_type: str = "access") -> Optional[str]:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=["HS256"], issuer=s.jwt_issuer)
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload.get("sub")


def _extract_token(request: Request, credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    if credentials and credentials.credentials:
        return credentials.credentials
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:]
    for name in ("rlabs_access", "rlabs_token"):
        if request.cookies.get(name):
            return request.cookies[name]
    return None


async def require_admin(request: Request,
                        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> str:
    token = _extract_token(request, credentials)
    email = decode_token(token) if token else None
    if not email:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated",
                            headers={"WWW-Authenticate": "Bearer"})
    db = get_db()
    admin = await db["admins"].find_one({"emails": email.lower()})
    if not admin:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return email


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
