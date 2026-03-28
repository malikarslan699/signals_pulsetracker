from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.auth import get_current_active_user
from app.core.exceptions import NotFoundError, SubscriptionRequiredError, ValidationError
from app.database import get_db
from app.models.user import User
from app.redis_client import RedisClient, get_redis_client
from app.services.mailer import send_email
from app.services.alert_service import AlertService
from app.services.system_config_service import load_system_config

router = APIRouter(prefix="/alerts", tags=["Alerts"])
settings = get_settings()


# ---------------------------------------------------------------------------
# Inline Pydantic models
# ---------------------------------------------------------------------------
class AlertConfigCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    channel: str = Field(pattern=r"^(telegram|email|webhook)$")
    webhook_url: Optional[str] = Field(default=None, max_length=500)
    min_confidence: int = Field(default=70, ge=0, le=100)
    directions: List[str] = Field(default=["LONG", "SHORT"])
    timeframes: List[str] = Field(default=["1H", "4H"])
    markets: List[str] = Field(default=["crypto"])
    pairs: Optional[List[str]] = None
    is_active: bool = True


class AlertConfigUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    channel: Optional[str] = Field(default=None, pattern=r"^(telegram|email|webhook)$")
    webhook_url: Optional[str] = Field(default=None, max_length=500)
    min_confidence: Optional[int] = Field(default=None, ge=0, le=100)
    directions: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    markets: Optional[List[str]] = None
    pairs: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AlertConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    channel: str
    webhook_url: Optional[str] = None
    min_confidence: int
    directions: List[str]
    timeframes: List[str]
    markets: List[str]
    pairs: Optional[List[str]] = None
    is_active: bool
    created_at: datetime


class TestAlertRequest(BaseModel):
    channel: Optional[str] = Field(default=None, pattern=r"^(telegram|email|webhook)$")
    webhook_url: Optional[str] = Field(default=None, max_length=500)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _require_alert_plan(user: User) -> None:
    """Raise SubscriptionRequiredError if user cannot manage alerts."""
    if user.plan not in ("monthly", "yearly", "lifetime", "trial") and not user.is_admin:
        raise SubscriptionRequiredError(
            "Alert management requires a trial or paid plan.",
            required_plan="trial",
        )


def _require_telegram_connected(user: User) -> None:
    """Raise ValidationError if user wants telegram alerts but has no chat_id."""
    if not user.telegram_chat_id:
        raise ValidationError(
            "You must connect your Telegram account before creating a Telegram alert. "
            "Use POST /auth/connect-telegram to link your account."
        )


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=list[AlertConfigResponse],
    summary="List the current user's alert configurations",
)
async def list_alerts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[AlertConfigResponse]:
    """Return all alert configurations owned by the current user."""
    service = AlertService(db)
    configs = await service.get_user_alerts(current_user.id)
    return [AlertConfigResponse.model_validate(c) for c in configs]


# ---------------------------------------------------------------------------
# POST /
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=AlertConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new alert configuration",
)
async def create_alert(
    payload: AlertConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlertConfigResponse:
    """
    Create a new alert configuration.
    Requires monthly/lifetime subscription and telegram connected (for telegram channel).
    """
    _require_alert_plan(current_user)

    if payload.channel == "telegram":
        _require_telegram_connected(current_user)

    service = AlertService(db)
    try:
        config = await service.create_alert(
            user_id=current_user.id,
            alert_data=payload.model_dump(),
        )
    except ValueError as exc:
        raise ValidationError(str(exc))

    return AlertConfigResponse.model_validate(config)


# ---------------------------------------------------------------------------
# PUT /{id}
# ---------------------------------------------------------------------------
@router.put(
    "/{alert_id}",
    response_model=AlertConfigResponse,
    summary="Update an existing alert configuration",
)
async def update_alert(
    alert_id: UUID,
    payload: AlertConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlertConfigResponse:
    """
    Update an alert configuration. Only the owner may update their own alerts.
    """
    _require_alert_plan(current_user)

    # If switching to telegram, ensure it's connected
    if payload.channel == "telegram":
        _require_telegram_connected(current_user)

    service = AlertService(db)
    try:
        config = await service.update_alert(
            alert_id=alert_id,
            user_id=current_user.id,
            data=payload.model_dump(exclude_none=True),
        )
    except ValueError as exc:
        detail = str(exc)
        if "not found" in detail.lower():
            raise NotFoundError("AlertConfig", alert_id)
        raise ValidationError(detail)

    return AlertConfigResponse.model_validate(config)


# ---------------------------------------------------------------------------
# DELETE /{id}
# ---------------------------------------------------------------------------
@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete an alert configuration",
)
async def delete_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Delete the specified alert configuration. Only the owner may delete."""
    service = AlertService(db)
    try:
        await service.delete_alert(alert_id=alert_id, user_id=current_user.id)
    except ValueError as exc:
        detail = str(exc)
        if "not found" in detail.lower():
            raise NotFoundError("AlertConfig", alert_id)
        raise ValidationError(detail)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# POST /test
# ---------------------------------------------------------------------------
@router.post(
    "/test",
    summary="Send a test Telegram message to the current user",
)
async def test_alert(
    payload: TestAlertRequest = Body(default_factory=TestAlertRequest),
    current_user: User = Depends(get_current_active_user),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    """
    Send a test Telegram message to verify the user's Telegram integration.
    Uses the user's connected telegram_chat_id by default.
    """
    channel = payload.channel or "telegram"

    if channel == "telegram":
        if not current_user.telegram_chat_id:
            raise ValidationError(
                "No Telegram account connected. "
                "Use POST /auth/connect-telegram first."
            )

        config = await load_system_config(redis)
        bot_token = config.integrations.telegram_bot_token or settings.TELEGRAM_BOT_TOKEN
        if not bot_token:
            raise ValidationError("Telegram bot is not configured on this server.")

        message = (
            "✅ *PulseSignal Pro* — Test Alert\n\n"
            "Your Telegram alerts are working correctly!\n"
            "You will receive trading signals in this chat.\n\n"
            "🔗 [Visit PulseSignal Pro](https://signals.pulsetracker.net)"
        )
        url = (
            f"https://api.telegram.org/bot{bot_token}/sendMessage"
        )
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": current_user.telegram_chat_id,
                        "text": message,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Telegram test failed for user {current_user.id}: "
                f"{exc.response.status_code} {exc.response.text}"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Telegram API error: {exc.response.text}",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not reach Telegram API: {exc}",
            )

        return {"status": "sent", "channel": "telegram", "chat_id": current_user.telegram_chat_id}

    elif channel == "webhook":
        if not payload.webhook_url:
            raise ValidationError("webhook_url is required for webhook test.")

        test_payload = {
            "event": "test",
            "message": "PulseSignal Pro webhook test — this is a test delivery.",
            "user": current_user.username,
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    payload.webhook_url,
                    json=test_payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "PulseSignal-Pro/1.0",
                    },
                )
                resp.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Webhook delivery failed: {exc}",
            )

        return {"status": "sent", "channel": "webhook", "url": payload.webhook_url}

    else:
        config = await load_system_config(redis)
        sent = await send_email(
            smtp=config.smtp,
            to_email=current_user.email,
            subject="PulseSignal Pro — Test Email Alert",
            text_body=(
                "This is a test email from PulseSignal Pro. "
                "Your email alert channel is configured correctly."
            ),
            html_body=(
                "<p>This is a <b>test email</b> from PulseSignal Pro.</p>"
                "<p>Your email alert channel is configured correctly.</p>"
            ),
        )
        if not sent:
            raise ValidationError(
                "Email alert test failed. Check SMTP settings in admin config."
            )
        return {
            "status": "sent",
            "channel": "email",
            "to": current_user.email,
        }
