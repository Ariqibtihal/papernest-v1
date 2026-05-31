from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.rate_limit import limiter
from app.db.session import get_async_session
from models.user import User
from schemas.auth import Token, UserLogin, UserOut, UserRegister
from services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    create_user_session,
    get_user_by_email,
    revoke_refresh_token,
    validate_refresh_token,
    verify_token,
)

router = APIRouter()


# ── Request body schemas for token endpoints ──────────────────────────────────


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: UserRegister,
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Register a new user with email and password."""
    existing_user = await get_user_by_email(session, data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = await create_user(
        session=session,
        email=data.email,
        password=data.password,
        full_name=data.full_name,
    )
    logger.info(f"User registered: {data.email}")
    return user


@router.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: UserLogin,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Login with email and password, return JWT tokens."""
    user = await authenticate_user(session, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(user_id=user.id)
    await create_user_session(session=session, user_id=user.id, refresh_token=refresh_token)
    logger.info(f"User logged in: {data.email}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 15 * 60,
    }


@router.post("/auth/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    body: RefreshRequest,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Refresh access token with refresh token rotation.

    The old refresh token is revoked and a new one is issued on every call.
    If the same refresh token is used twice (replay attack), the second call
    will fail because the token was already revoked.
    """
    payload = verify_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from None

    # Validate old token — this also checks expiry and revocation status
    user_session = await validate_refresh_token(session, body.refresh_token, user_id)
    if not user_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or revoked",
        )

    # ROTATION: revoke the old token before issuing a new one
    user_session.revoked = True
    await session.commit()
    await session.refresh(user_session)  # ensure revoked=True is visible to subsequent reads
    logger.info(f"Rotated refresh token for user {user_id}")

    # Issue new token pair
    new_access_token = create_access_token(data={"sub": str(user_id)})
    new_refresh_token = create_refresh_token(user_id=user_id)
    await create_user_session(session=session, user_id=user_id, refresh_token=new_refresh_token)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": 15 * 60,
    }


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Logout and revoke refresh token. Token must be sent in the request body."""
    revoked = await revoke_refresh_token(session, current_user.id, body.refresh_token)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token")
    logger.info(f"User logged out: {current_user.email}")


@router.get("/auth/me", response_model=UserOut)
async def get_current_user_profile(current_user: CurrentUser) -> User:
    """Get current user profile."""
    return current_user
