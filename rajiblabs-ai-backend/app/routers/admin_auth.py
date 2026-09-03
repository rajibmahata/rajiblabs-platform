"""Admin auth — dual-email single identity, env password, hashed. POST /api/admin/auth/*"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from app.auth.dependencies import (check_login_rate_limit, create_access_token,
                                   create_refresh_token, require_admin)
from app.auth.utils import hash_password, verify_password
from app.config import get_settings
from app.database import get_db, utcnow
from app.schemas import LoginIn
from app.services.notify import audit

router = APIRouter(prefix="/api/admin/auth")


async def _ensure_admin():
    """Create single admin on first run from env; never overwrite existing."""
    s = get_settings()
    db = get_db()
    if await db["admins"].count_documents({}) > 0:
        return
    if not s.admin_initial_password:
        return  # configured later via env
    await db["admins"].insert_one({
        "emails": s.admin_email_list, "password_hash": hash_password(s.admin_initial_password),
        "created_at": utcnow(), "last_login_at": None})


@router.post("/login")
async def login(body: LoginIn, request: Request, response: Response):
    check_login_rate_limit(request.client.host if request.client else "unknown")
    await _ensure_admin()
    s = get_settings()
    db = get_db()
    email = body.email.strip().lower()
    if email not in s.admin_email_list:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    admin = await db["admins"].find_one({"emails": email})
    if not admin or not verify_password(body.password, admin["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    await db["admins"].update_one({"_id": admin["_id"]}, {"$set": {"last_login_at": utcnow()}})
    access, refresh = create_access_token(email), create_refresh_token(email)
    response.set_cookie("rlabs_access", access, httponly=True, secure=True, samesite="strict",
                        max_age=900, path="/")
    response.set_cookie("rlabs_refresh", refresh, httponly=True, secure=True, samesite="strict",
                        max_age=7 * 86400, path="/api/admin/auth")
    await audit(email, "LOGIN", "admin")
    return {"access_token": access, "email": email}


@router.post("/logout")
async def logout(response: Response, email: str = Depends(require_admin)):
    response.delete_cookie("rlabs_access", path="/")
    response.delete_cookie("rlabs_refresh", path="/api/admin/auth")
    await audit(email, "LOGOUT", "admin")
    return {"ok": True}


@router.get("/me")
async def me(email: str = Depends(require_admin)):
    return {"email": email, "role": "admin"}
