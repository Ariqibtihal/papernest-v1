from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from models.user import User, UserSession
from utils.security import hash_password, verify_password

settings = get_settings()

# Account lockout configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Precomputed bcrypt hash of a random string. Used to equalize timing
# between "user not found" and "wrong password" code paths in
# authenticate_user(). Generated once at module load to avoid the
# computation cost on every login attempt.
_DUMMY_BCRYPT_HASH = hash_password(secrets.token_urlsafe(32))


def _now() -> datetime:
    """Return current UTC time as timezone-aware datetime. Single source of truth."""
    return datetime.now(UTC)


def _make_naive(dt: datetime) -> datetime:
    """Strip timezone info for comparison with naive DB datetimes (SQLite stores naive UTC)."""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def create_access_token(data: dict[str, Any]) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = _now() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(user_id: int) -> str:
    """Create a JWT refresh token with a unique jti to prevent token reuse."""
    expire = _now() + timedelta(days=settings.refresh_token_expire_days)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_hex(16),  # unique per token — prevents identical tokens
    }
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify and decode a JWT token. Returns None if invalid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        logger.debug(f"Token verification failed: {e}")
        return None


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    """Create a new user with hashed password."""
    hashed_password = hash_password(password)
    user = User(
        email=email,
        password_hash=hashed_password,
        full_name=full_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info(f"Created new user: {email}")
    return user


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """
    Authenticate by email + password.

    Returns the User on success, None on invalid credentials, raises 423 on
    locked account.

    Defense against email enumeration via timing: when the email does not
    exist, we still run a bcrypt verify against a dummy hash so total
    response time matches the "wrong password" path. Without this, an
    attacker can distinguish "email registered" (slow) from "email not
    registered" (fast) by measuring response latency.
    """
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Use naive UTC for comparison with DB values (SQLite stores naive datetimes)
    now_naive = _make_naive(_now())

    if not user:
        # Dummy verify to equalize timing with the real-user wrong-password path.
        # _DUMMY_BCRYPT_HASH is a precomputed hash of a random string.
        verify_password(password, _DUMMY_BCRYPT_HASH)
        logger.debug(f"User not found: {email}")
        return None

    # Check if account is locked
    if user.locked_until and user.locked_until > now_naive:
        delta = user.locked_until - now_naive
        remaining = max(0, int(delta.total_seconds() // 60))
        logger.warning(f"Account locked: {email}, remaining: {remaining} minutes")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked due to too many failed login attempts. Try again in {remaining} minutes.",
        )

    # Reset lock if expired
    if user.locked_until and user.locked_until <= now_naive:
        user.locked_until = None
        user.failed_login_attempts = 0
        logger.info(f"Account lock expired and reset: {email}")

    if not user.is_active:
        logger.debug(f"User account is inactive: {email}")
        return None

    # Verify password
    if not verify_password(password, user.password_hash):
        # Increment failed attempts
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = now_naive + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            await session.commit()
            logger.warning(f"Account locked after {MAX_FAILED_ATTEMPTS} failed attempts: {email}")
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked for {LOCKOUT_DURATION_MINUTES} minutes due to too many failed login attempts.",
            )

        await session.commit()
        logger.debug(
            f"Invalid password for user: {email}, attempts: {user.failed_login_attempts}/{MAX_FAILED_ATTEMPTS}"
        )
        return None

    # Successful login - reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = now_naive
    await session.commit()

    logger.info(f"User authenticated successfully: {email}")
    return user


async def create_user_session(
    session: AsyncSession,
    user_id: int,
    refresh_token: str,
) -> UserSession:
    """Create a new user session with refresh token."""
    # Hash the refresh token for storage
    refresh_token_hash = hash_password(refresh_token)

    now_naive = _make_naive(_now())
    expires_at = now_naive + timedelta(days=settings.refresh_token_expire_days)

    user_session = UserSession(
        user_id=user_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at,
    )
    session.add(user_session)
    await session.commit()
    await session.refresh(user_session)

    return user_session


async def validate_refresh_token(
    session: AsyncSession,
    refresh_token: str,
    user_id: int,
) -> UserSession | None:
    """Validate a refresh token and return the session if valid."""
    now_naive = _make_naive(_now())
    result = await session.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked == False,  # noqa: E712
            UserSession.expires_at > now_naive,
        )
    )
    sessions = result.scalars().all()

    for user_session in sessions:
        if verify_password(refresh_token, user_session.refresh_token_hash):
            return user_session

    return None


async def revoke_refresh_token(session: AsyncSession, user_id: int, refresh_token: str) -> bool:
    """Revoke a refresh token."""
    user_session = await validate_refresh_token(session, refresh_token, user_id)

    if user_session:
        user_session.revoked = True
        await session.commit()
        logger.info(f"Revoked refresh token for user {user_id}")
        return True

    return False


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Get user by ID."""
    return await session.get(User, user_id)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Get user by email."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
