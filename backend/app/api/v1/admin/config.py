from __future__ import annotations

from typing import Optional

import httpx
from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel, EmailStr, Field

from app.config import get_settings
from app.core.auth import get_current_active_user, require_role
from app.models.user import User
from app.redis_client import RedisClient, get_redis_client
from app.services.mailer import check_smtp_connection, send_email
from app.services.system_config_service import (
    ProviderHealthState,
    SystemConfig,
    load_system_config,
    load_provider_health,
    mask_sensitive_config,
    save_system_config,
    set_provider_health,
)

router = APIRouter(
    prefix="/admin/config",
    tags=["Admin — Config"],
    dependencies=[Depends(require_role("admin", "owner"))],
)
settings = get_settings()


class SMTPCheckRequest(BaseModel):
    test_email: Optional[EmailStr] = None


class TelegramCheckRequest(BaseModel):
    chat_id: Optional[str] = Field(default=None, max_length=64)
    send_test_message: bool = False

# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=SystemConfig,
    summary="Get current system configuration",
)
async def get_config(
    redis: RedisClient = Depends(get_redis_client),
    current_admin: User = Depends(get_current_active_user),
) -> SystemConfig:
    """
    Return the current system configuration.
    Admin users receive masked secrets; owner receives full values.
    """
    config = await load_system_config(redis)
    if current_admin.role not in ("owner", "superadmin"):
        return mask_sensitive_config(config)
    return config


# ---------------------------------------------------------------------------
# PUT /
# ---------------------------------------------------------------------------
@router.put(
    "/",
    response_model=SystemConfig,
    summary="Save system configuration",
)
async def update_config(
    payload: SystemConfig,
    redis: RedisClient = Depends(get_redis_client),
    current_admin: User = Depends(get_current_active_user),
) -> SystemConfig:
    """
    Persist the system configuration to Redis.
    Sensitive fields (SMTP/API tokens) are owner-only.
    """
    current = await load_system_config(redis)

    # Owner-only: SMTP credentials + integration API keys/tokens.
    if current_admin.role not in ("owner", "superadmin"):
        payload.smtp = current.smtp
        payload.integrations = current.integrations

    await save_system_config(redis, payload)

    logger.info(
        f"System config updated by {current_admin.role} {current_admin.id}: "
        f"scanner_interval={payload.scanner_interval_minutes}m "
        f"min_confidence={payload.min_signal_confidence} "
        f"maintenance={payload.maintenance_mode} "
        f"require_email_verification={payload.auth.require_email_verification}"
    )

    if current_admin.role not in ("owner", "superadmin"):
        return mask_sensitive_config(payload)
    return payload


@router.get(
    "/provider-status",
    response_model=ProviderHealthState,
    summary="Get SMTP/Telegram provider health status",
)
async def get_provider_status(
    redis: RedisClient = Depends(get_redis_client),
) -> ProviderHealthState:
    return await load_provider_health(redis)


@router.post(
    "/check-smtp",
    response_model=ProviderHealthState,
    summary="Check SMTP connectivity and optionally send a test email",
)
async def check_smtp_provider(
    payload: SMTPCheckRequest,
    redis: RedisClient = Depends(get_redis_client),
    current_admin: User = Depends(get_current_active_user),
) -> ProviderHealthState:
    config = await load_system_config(redis)

    missing_fields: list[str] = []
    if not config.smtp.enabled:
        missing_fields.append("enabled")
    if not config.smtp.host:
        missing_fields.append("host")
    if not config.smtp.from_email:
        missing_fields.append("from_email")

    ok, message = await check_smtp_connection(config.smtp)
    details: dict = {
        "host": config.smtp.host,
        "port": config.smtp.port,
        "from_email": config.smtp.from_email,
        "missing_fields": missing_fields,
    }

    if missing_fields:
        message = (
            "SMTP is not fully configured. Missing: "
            + ", ".join(missing_fields)
            + "."
        )
        ok = False

    if ok and payload.test_email:
        sent = await send_email(
            smtp=config.smtp,
            to_email=str(payload.test_email),
            subject="PulseSignal Pro SMTP Test",
            text_body=(
                "SMTP test successful. This confirms owner SMTP settings are working."
            ),
            html_body=(
                "<p><b>SMTP test successful.</b></p>"
                "<p>This confirms owner SMTP settings are working.</p>"
            ),
        )
        details["test_email"] = str(payload.test_email)
        details["test_email_sent"] = sent
        if sent:
            message = f"{message} Test email sent successfully."
        else:
            ok = False
            message = "SMTP connected, but test email delivery failed."

    status = "healthy" if ok else "issue"
    state = await set_provider_health(
        redis=redis,
        provider="smtp",
        status=status,
        message=message,
        details=details,
    )

    logger.info(
        f"SMTP provider check by {current_admin.role} {current_admin.id}: {status} - {message}"
    )
    return state


@router.post(
    "/check-telegram",
    response_model=ProviderHealthState,
    summary="Check Telegram bot token and optionally send a test message",
)
async def check_telegram_provider(
    payload: TelegramCheckRequest,
    redis: RedisClient = Depends(get_redis_client),
    current_admin: User = Depends(get_current_active_user),
) -> ProviderHealthState:
    config = await load_system_config(redis)
    token = config.integrations.telegram_bot_token or settings.TELEGRAM_BOT_TOKEN

    if not token:
        state = await set_provider_health(
            redis=redis,
            provider="telegram",
            status="issue",
            message="Telegram bot token is not configured.",
            details={},
        )
        return state

    url = f"https://api.telegram.org/bot{token}/getMe"
    details: dict = {}

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.post(url)
            data = resp.json()
            if not resp.is_success or not data.get("ok"):
                message = "Telegram bot token check failed."
                details["http_status"] = resp.status_code
                details["error"] = data.get("description") if isinstance(data, dict) else ""
                return await set_provider_health(
                    redis=redis,
                    provider="telegram",
                    status="issue",
                    message=message,
                    details=details,
                )

            result = data.get("result", {}) if isinstance(data, dict) else {}
            username = result.get("username", "")
            details["bot_username"] = f"@{username}" if username else ""
            details["bot_id"] = result.get("id")
            message = f"Telegram connected as @{username}." if username else "Telegram bot connected."

            if payload.send_test_message:
                chat_id = payload.chat_id or config.integrations.telegram_vip_channel_id
                if chat_id:
                    send_url = f"https://api.telegram.org/bot{token}/sendMessage"
                    send_resp = await client.post(
                        send_url,
                        json={
                            "chat_id": str(chat_id),
                            "text": "PulseSignal Pro test message: Telegram provider is healthy.",
                        },
                    )
                    send_data = send_resp.json() if send_resp.headers.get("content-type", "").startswith("application/json") else {}
                    if send_resp.is_success and isinstance(send_data, dict) and send_data.get("ok"):
                        message += " Test message sent."
                        details["test_chat_id"] = str(chat_id)
                    else:
                        return await set_provider_health(
                            redis=redis,
                            provider="telegram",
                            status="issue",
                            message="Telegram bot connected, but test message failed.",
                            details={
                                **details,
                                "test_chat_id": str(chat_id),
                                "error": send_data.get("description", "Unknown Telegram send error")
                                if isinstance(send_data, dict)
                                else "Unknown Telegram send error",
                            },
                        )
                else:
                    message += " No chat ID provided for test message."

            state = await set_provider_health(
                redis=redis,
                provider="telegram",
                status="healthy",
                message=message,
                details=details,
            )
            logger.info(
                f"Telegram provider check by {current_admin.role} {current_admin.id}: healthy"
            )
            return state
    except Exception as exc:
        state = await set_provider_health(
            redis=redis,
            provider="telegram",
            status="issue",
            message=f"Telegram check failed: {exc}",
            details={},
        )
        logger.warning(
            f"Telegram provider check by {current_admin.role} {current_admin.id} failed: {exc}"
        )
        return state



@router.post(
    "/purge-signals",
    summary="Purge low-quality signals from Redis and mark them expired in DB",
)
async def purge_low_quality_signals_endpoint(
    min_confidence: int = 75,
    current_admin: User = Depends(require_role("admin", "owner")),
):
    """
    Immediately remove all active signals below min_confidence from Redis
    and mark them as expired in PostgreSQL.  Also deduplicates the active set.
    """
    try:
        from workers.cleanup_task import purge_low_quality_signals
        result = purge_low_quality_signals.apply_async(
            kwargs={"min_confidence": min_confidence},
            queue="default",
        )
        return {"status": "queued", "task_id": result.id, "min_confidence": min_confidence}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
