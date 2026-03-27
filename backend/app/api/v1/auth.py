from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, EmailStr
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.database import get_db
from app.models.user import User
from app.redis_client import RedisClient, get_redis_client
from app.schemas.user import (
    EmailVerificationRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.services.mailer import build_verification_email, send_email
from app.services.system_config_service import load_system_config

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> TokenResponse:
    """
    Create a new user account. The account starts on a 24-hour trial plan.
    Returns access and refresh JWT tokens.
    """
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise ConflictError("An account with this email already exists.")

    # Check username uniqueness
    result = await db.execute(select(User).where(User.username == payload.username))
    if result.scalar_one_or_none():
        raise ConflictError("This username is already taken.")

    config = await load_system_config(redis)

    # Create user with configurable trial window (default: 24h)
    trial_expires = datetime.now(tz=timezone.utc) + timedelta(
        hours=config.auth.trial_hours
    )
    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        role="user",
        plan="trial",
        plan_expires_at=trial_expires,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    logger.info(f"New user registered: {user.email} (id={user.id})")

    require_verification = bool(config.auth.require_email_verification)

    if require_verification:
        token = secrets.token_urlsafe(24)
        verify_key = f"auth:verify_email:{token}"
        ttl = 60 * 60 * 24  # 24h
        await redis._r.set(verify_key, str(user.id), ex=ttl)

        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        subject, text_body, html_body = build_verification_email(verify_url)
        sent = await send_email(
            config.smtp,
            to_email=user.email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )

        return TokenResponse(
            user=UserResponse.model_validate(user),
            requires_email_verification=True,
            verification_email_sent=sent,
            message=(
                "Please verify your email before signing in."
                if sent
                else "Email verification is required, but SMTP is not configured."
            ),
        )

    # Email verification disabled -> immediate login flow.
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_seconds,
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive JWT tokens",
)
async def login(
    payload: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> TokenResponse:
    """
    Verify credentials, check account status, bind device fingerprint, return tokens.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user: Optional[User] = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")

    if not user.is_active:
        raise AuthenticationError("Account is deactivated. Contact support.")

    config = await load_system_config(redis)
    if config.auth.require_email_verification and not user.is_verified:
        raise AuthenticationError(
            "Email is not verified. Please verify your email first."
        )

    # Device fingerprint — use IP + User-Agent as a lightweight fingerprint
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "")
    device_fp = f"{client_ip}:{user_agent[:64]}"

    # Bind fingerprint on first login or if it matches
    if user.device_fingerprint is None:
        user.device_fingerprint = device_fp
        logger.info(f"Device fingerprint set for user {user.id}")
    # Note: we don't block on mismatch here — just update (policy decision)

    logger.info(f"User logged in: {user.email} (id={user.id})")

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_seconds,
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token using a valid refresh token",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> TokenResponse:
    """
    Exchange a valid refresh token for a new access token.
    The old refresh token is blacklisted in Redis (rotation).
    """
    token_payload = decode_token(payload.refresh_token)

    if token_payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type — expected refresh token.")

    jti: Optional[str] = token_payload.get("jti")
    if jti and await redis.is_token_blacklisted(jti):
        raise AuthenticationError("Refresh token has been revoked.")

    user_id: Optional[str] = token_payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token is missing subject.")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or deactivated.")

    config = await load_system_config(redis)
    if config.auth.require_email_verification and not user.is_verified:
        raise AuthenticationError(
            "Email is not verified. Please verify your email first."
        )

    # Blacklist old refresh token
    if jti:
        exp: int = token_payload.get("exp", 0)
        now_ts = int(datetime.now(tz=timezone.utc).timestamp())
        ttl = max(exp - now_ts, 1)
        await redis.blacklist_token(jti, ttl)

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_seconds,
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------
@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Invalidate the current access token",
)
async def logout(
    current_user: User = Depends(get_current_active_user),
    redis: RedisClient = Depends(get_redis_client),
    request: Request = None,
) -> Response:
    """
    Blacklist the current access token's JTI in Redis.
    The token remains syntactically valid but is rejected on all future requests.
    """
    auth_header = request.headers.get("Authorization", "") if request else ""
    token = auth_header.removeprefix("Bearer ").strip()

    if token:
        try:
            payload = decode_token(token)
            jti: Optional[str] = payload.get("jti")
            if jti:
                exp: int = payload.get("exp", 0)
                now_ts = int(datetime.now(tz=timezone.utc).timestamp())
                ttl = max(exp - now_ts, 1)
                await redis.blacklist_token(jti, ttl)
                logger.info(f"Token blacklisted (logout) for user {current_user.id}, jti={jti}")
        except Exception:
            pass  # Token may already be expired — logout is still successful

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the currently authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# GET /verify-email
# ---------------------------------------------------------------------------
@router.get(
    "/verify-email",
    summary="Verify email using one-time token",
)
async def verify_email(
    token: str = Query(..., min_length=10),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    verify_key = f"auth:verify_email:{token}"
    user_id = await redis._r.get(verify_key)
    if not user_id:
        raise ValidationError("Verification link is invalid or expired.")

    try:
        uid = uuid.UUID(str(user_id))
    except Exception:
        raise ValidationError("Verification token is malformed.")

    result = await db.execute(select(User).where(User.id == uid))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User", str(uid))

    user.is_verified = True
    await db.flush()
    await redis._r.delete(verify_key)

    logger.info(f"Email verified for user {user.id}")
    return {"status": "verified", "message": "Email verified successfully."}


# ---------------------------------------------------------------------------
# POST /resend-verification
# ---------------------------------------------------------------------------
@router.post(
    "/resend-verification",
    summary="Resend email verification link",
)
async def resend_verification(
    payload: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    result = await db.execute(select(User).where(User.email == payload.email))
    user: Optional[User] = result.scalar_one_or_none()

    # Generic response to avoid account enumeration.
    generic = {
        "status": "ok",
        "message": "If the email exists, a verification link has been sent.",
    }

    if not user or user.is_verified:
        return generic

    config = await load_system_config(redis)
    if not config.auth.require_email_verification:
        return generic

    token = secrets.token_urlsafe(24)
    verify_key = f"auth:verify_email:{token}"
    ttl = 60 * 60 * 24
    await redis._r.set(verify_key, str(user.id), ex=ttl)

    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject, text_body, html_body = build_verification_email(verify_url)
    sent = await send_email(
        config.smtp,
        to_email=user.email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
    if sent:
        logger.info(f"Verification email resent: user={user.id}")

    return generic


# ---------------------------------------------------------------------------
# PUT /me
# ---------------------------------------------------------------------------
@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update the current user's profile",
)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update editable profile fields. Only non-null fields in the payload are applied.
    """
    if payload.username is not None and payload.username != current_user.username:
        result = await db.execute(
            select(User).where(
                User.username == payload.username,
                User.id != current_user.id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictError("This username is already taken.")
        current_user.username = payload.username

    if payload.telegram_username is not None:
        current_user.telegram_username = payload.telegram_username

    if payload.telegram_chat_id is not None:
        current_user.telegram_chat_id = payload.telegram_chat_id

    if payload.device_fingerprint is not None:
        current_user.device_fingerprint = payload.device_fingerprint

    await db.flush()
    logger.info(f"User profile updated: {current_user.id}")
    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# POST /connect-telegram
# ---------------------------------------------------------------------------
@router.post(
    "/connect-telegram",
    summary="Link a Telegram account via a verification code",
)
async def connect_telegram(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    """
    Generate a one-time Telegram verification code.
    The code is stored in Redis for 10 minutes. The user should send this code
    to the PulseSignal Telegram bot to link their account.
    """
    verification_code = str(secrets.randbelow(900000) + 100000)  # 6-digit numeric code
    redis_key = f"telegram:verify:{verification_code}"

    # Store user_id → verification code mapping
    await redis._r.set(redis_key, str(current_user.id), ex=600)  # 10 minutes

    logger.info(
        f"Telegram verification code generated for user {current_user.id}: {verification_code}"
    )

    return {
        "verification_code": verification_code,
        "expires_in_seconds": 600,
        "instructions": (
            "Send this code to the PulseSignal Pro Telegram bot "
            "(@PulseSignalProBot) to link your account."
        ),
        "bot_url": "https://t.me/PulseSignalProBot",
    }


# ---------------------------------------------------------------------------
# POST /forgot-password — send OTP to email if it exists in DB
# ---------------------------------------------------------------------------
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


@router.post("/forgot-password", summary="Request a password reset OTP")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    """
    If the email exists in the database, send a 6-digit OTP to it.
    Always returns the same response to avoid leaking whether the email exists.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user: Optional[User] = result.scalar_one_or_none()

    if user:
        otp = str(secrets.randbelow(900000) + 100000)  # 6-digit
        redis_key = f"auth:password_reset:{payload.email}"
        await redis._r.set(redis_key, otp, ex=600)  # 10 minutes

        # Send OTP via SMTP
        try:
            smtp_cfg = await load_system_config(redis)
            subject = "PulseSignal Pro — Password Reset OTP"
            text_body = (
                f"Your password reset code is: {otp}\n\n"
                f"This code expires in 10 minutes.\n"
                f"If you did not request a password reset, ignore this email."
            )
            html_body = (
                f"<p>Your password reset code is:</p>"
                f"<h2 style='letter-spacing:4px;font-size:32px'>{otp}</h2>"
                f"<p>This code expires in <b>10 minutes</b>.</p>"
                f"<p style='color:#888'>If you did not request a password reset, ignore this email.</p>"
            )
            await send_email(smtp_cfg.smtp, payload.email, subject, text_body, html_body)
            logger.info(f"Password reset OTP sent to {payload.email}")
        except Exception as e:
            logger.warning(f"Could not send reset OTP to {payload.email}: {e}")

    # Always return same message — don't reveal if email exists
    return {"message": "If that email is registered, an OTP has been sent."}


@router.post("/reset-password", summary="Reset password using OTP")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    """
    Validate the OTP and update the user's password.
    """
    if len(payload.new_password) < 8:
        raise ValidationError("Password must be at least 8 characters.")

    redis_key = f"auth:password_reset:{payload.email}"
    stored_otp = await redis._r.get(redis_key)

    if not stored_otp or stored_otp != payload.otp:
        raise AuthenticationError("Invalid or expired OTP.")

    result = await db.execute(select(User).where(User.email == payload.email))
    user: Optional[User] = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("Invalid or expired OTP.")

    user.password_hash = get_password_hash(payload.new_password)
    await redis._r.delete(redis_key)
    await db.flush()

    logger.info(f"Password reset successful for user {user.id}")
    return {"message": "Password has been reset successfully. You can now sign in."}
