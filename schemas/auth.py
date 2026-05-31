from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str | None = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        """Sanitize full name."""
        if v:
            # Remove any HTML tags
            v = re.sub(r"<[^>]+>", "", v)
            # Remove excessive whitespace
            v = " ".join(v.split())
            # Prevent very long names
            if len(v) > 255:
                raise ValueError("Full name is too long")
        return v


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str


class Token(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sub: str  # user_id
    exp: datetime
    type: str  # "access" or "refresh"


class UserOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime
    last_login: datetime | None
