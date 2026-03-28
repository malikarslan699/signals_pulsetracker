from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

COMMON_EMAIL_DOMAIN_TYPOS: dict[str, str] = {
    "gamil.com": "gmail.com",
    "gmai.com": "gmail.com",
    "gmail.co": "gmail.com",
    "gmail.con": "gmail.com",
    "gmaill.com": "gmail.com",
    "gmial.com": "gmail.com",
    "gnail.com": "gmail.com",
    "hotnail.com": "hotmail.com",
    "hotmai.com": "hotmail.com",
    "yaho.com": "yahoo.com",
    "yhoo.com": "yahoo.com",
    "outlok.com": "outlook.com",
    "outllok.com": "outlook.com",
}


def _validate_email_domain_typos(value: EmailStr) -> str:
    email = str(value).strip().lower()
    if "@" not in email:
        return str(value)

    _local, domain = email.rsplit("@", 1)
    suggestion = COMMON_EMAIL_DOMAIN_TYPOS.get(domain)
    if suggestion:
        raise ValueError(
            f"Email domain '{domain}' looks incorrect. Did you mean '{suggestion}'?"
        )
    return email


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: EmailStr) -> str:
        return _validate_email_domain_typos(v)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: EmailStr) -> str:
        return _validate_email_domain_typos(v)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    username: str
    role: str
    plan: str
    plan_expires_at: Optional[datetime] = None
    market_access: str = "both"
    is_active: bool
    is_verified: bool
    qa_access: bool = False
    telegram_chat_id: Optional[int] = None
    telegram_username: Optional[str] = None
    created_at: datetime


class UserUpdate(BaseModel):
    """Fields the user can update themselves."""

    model_config = ConfigDict(str_strip_whitespace=True)

    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )
    telegram_username: Optional[str] = Field(default=None, max_length=100)
    telegram_chat_id: Optional[int] = None
    device_fingerprint: Optional[str] = Field(default=None, max_length=255)


class UserAdminUpdate(BaseModel):
    """Fields that only admins can modify."""

    model_config = ConfigDict(str_strip_whitespace=True)

    role: Optional[str] = Field(
        default=None, pattern=r"^(user|premium|admin|owner|superadmin|reseller)$"
    )
    plan: Optional[str] = Field(
        default=None, pattern=r"^(trial|monthly|yearly|lifetime)$"
    )
    plan_expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    qa_access: Optional[bool] = None
    market_access: Optional[str] = Field(
        default=None, pattern=r"^(crypto|forex|both)$"
    )


class TokenResponse(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 0  # seconds until access_token expiry
    user: UserResponse
    requires_email_verification: bool = False
    verification_email_sent: bool = False
    message: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: EmailStr) -> str:
        return _validate_email_domain_typos(v)


class EmailVerificationRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: EmailStr) -> str:
        return _validate_email_domain_typos(v)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v
