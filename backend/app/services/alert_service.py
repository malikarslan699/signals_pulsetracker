from __future__ import annotations

from typing import Optional
from uuid import UUID

import httpx
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.alert import AlertConfig
from app.models.signal import Signal
from app.models.user import User
from app.redis_client import RedisClient, get_redis
from app.services.mailer import build_signal_email, send_email
from app.services.system_config_service import load_system_config


def _calc_rr(entry: float, stop_loss: float, take_profit: float | None) -> float | None:
    try:
        if take_profit is None:
            return None
        risk = abs(float(entry) - float(stop_loss))
        if risk <= 0:
            return None
        reward = abs(float(take_profit) - float(entry))
        return round(reward / risk, 2)
    except Exception:
        return None


class AlertService:
    """Business logic for managing and dispatching alerts."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # CRUD for AlertConfig
    # ------------------------------------------------------------------
    async def get_user_alerts(self, user_id: UUID) -> list[AlertConfig]:
        """Return all alert configurations owned by a user."""
        result = await self._db.execute(
            select(AlertConfig)
            .where(AlertConfig.user_id == user_id)
            .order_by(AlertConfig.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_alert(self, user_id: UUID, alert_data: dict) -> AlertConfig:
        """
        Create a new alert configuration for the user.
        Validates the channel-specific requirements (e.g. webhook_url for webhook).
        """
        channel = alert_data.get("channel", "")
        if channel == "webhook" and not alert_data.get("webhook_url"):
            raise ValueError("webhook_url is required for webhook channel.")
        if channel not in ("telegram", "email", "webhook"):
            raise ValueError(f"Unsupported channel: {channel}")

        config = AlertConfig(
            user_id=user_id,
            channel=channel,
            webhook_url=alert_data.get("webhook_url"),
            min_confidence=alert_data.get("min_confidence", 70),
            directions=alert_data.get("directions", ["LONG", "SHORT"]),
            timeframes=alert_data.get("timeframes", ["1H", "4H"]),
            markets=alert_data.get("markets", ["crypto"]),
            pairs=alert_data.get("pairs"),
            is_active=alert_data.get("is_active", True),
        )
        self._db.add(config)
        await self._db.flush()
        logger.info(
            f"AlertConfig created: id={config.id} user={user_id} channel={channel}"
        )
        return config

    async def update_alert(
        self, alert_id: UUID, user_id: UUID, data: dict
    ) -> AlertConfig:
        """Update an existing alert config. Only the owner can update."""
        config = await self._get_owned_alert(alert_id, user_id)

        updatable_fields = {
            "channel",
            "webhook_url",
            "min_confidence",
            "directions",
            "timeframes",
            "markets",
            "pairs",
            "is_active",
        }
        for field, value in data.items():
            if field in updatable_fields and value is not None:
                setattr(config, field, value)

        if config.channel == "webhook" and not config.webhook_url:
            raise ValueError("webhook_url is required for webhook channel.")

        await self._db.flush()
        return config

    async def delete_alert(self, alert_id: UUID, user_id: UUID) -> None:
        """Delete an alert config. Only the owner can delete."""
        config = await self._get_owned_alert(alert_id, user_id)
        await self._db.delete(config)
        await self._db.flush()
        logger.info(f"AlertConfig {alert_id} deleted by user {user_id}.")

    # ------------------------------------------------------------------
    # Signal Matching & Dispatch
    # ------------------------------------------------------------------
    async def find_matching_users(self, signal: Signal) -> list[User]:
        """
        Return all users whose active alert configs match the given signal.
        Checks: confidence threshold, direction, timeframe, market, and symbol.
        """
        result = await self._db.execute(
            select(AlertConfig)
            .where(AlertConfig.is_active == True)  # noqa: E712
            .where(AlertConfig.min_confidence <= signal.confidence)
        )
        all_configs = list(result.scalars().all())

        matching_user_ids: set[UUID] = set()

        for config in all_configs:
            # Direction filter
            if config.directions and signal.direction not in config.directions:
                continue

            # Timeframe filter
            if config.timeframes and signal.timeframe not in config.timeframes:
                continue

            # Market filter
            if config.markets and signal.market not in config.markets:
                continue

            # Symbol filter (None = all pairs)
            if config.pairs and signal.symbol not in config.pairs:
                continue

            matching_user_ids.add(config.user_id)

        if not matching_user_ids:
            return []

        users_result = await self._db.execute(
            select(User)
            .where(User.id.in_(matching_user_ids))
            .where(User.is_active == True)  # noqa: E712
        )
        return list(users_result.scalars().all())

    async def dispatch_signal_alert(self, signal: Signal) -> None:
        """
        Find all users matching the signal's criteria and send them alerts
        through their configured channels.
        """
        users = await self.find_matching_users(signal)
        if not users:
            logger.debug(
                f"No matching users for signal {signal.id} ({signal.symbol})."
            )
            return

        logger.info(
            f"Dispatching alert for signal {signal.id} ({signal.symbol}) "
            f"to {len(users)} user(s)."
        )

        # Load alert configs for matched users
        user_ids = [u.id for u in users]
        configs_result = await self._db.execute(
            select(AlertConfig)
            .where(AlertConfig.user_id.in_(user_ids))
            .where(AlertConfig.is_active == True)  # noqa: E712
        )
        configs = list(configs_result.scalars().all())

        # Build a user → configs map
        user_map: dict[UUID, User] = {u.id: u for u in users}
        config_map: dict[UUID, list[AlertConfig]] = {}
        for config in configs:
            config_map.setdefault(config.user_id, []).append(config)

        for user_id, user_configs in config_map.items():
            user = user_map.get(user_id)
            if not user:
                continue
            for config in user_configs:
                try:
                    if config.channel == "telegram":
                        await self._send_telegram(user, signal)
                    elif config.channel == "webhook":
                        await self._send_webhook(config, signal)
                    elif config.channel == "email":
                        await self._send_email(user, signal)
                except Exception as exc:
                    logger.error(
                        f"Failed to send {config.channel} alert to user "
                        f"{user_id}: {exc}"
                    )

    # ------------------------------------------------------------------
    # Channel-specific delivery
    # ------------------------------------------------------------------
    async def _send_telegram(self, user: User, signal: Signal) -> None:
        """Send a signal alert via Telegram to the user's chat."""
        settings = get_settings()
        async with get_redis() as redis:
            config = await load_system_config(RedisClient(redis))
        if not config.notifications.enable_telegram_alerts:
            logger.debug("Telegram alerts disabled in system config.")
            return
        bot_token = (
            config.integrations.telegram_bot_token
            or settings.TELEGRAM_BOT_TOKEN
        )
        if not bot_token:
            logger.warning("Telegram bot token not configured.")
            return

        chat_id = user.telegram_chat_id
        if not chat_id:
            logger.debug(
                f"User {user.id} has no telegram_chat_id — skipping Telegram alert."
            )
            return

        direction_emoji = "📈" if signal.direction == "LONG" else "📉"
        probability_tp1 = (
            float(signal.pwin_tp1)
            if getattr(signal, "pwin_tp1", None) is not None
            else float(signal.confidence)
        )
        message = (
            f"{direction_emoji} *{signal.symbol}* — {signal.direction}\n"
            f"⏱ Timeframe: `{signal.timeframe}`\n"
            f"🎯 P(TP1): `{probability_tp1:.0f}%`\n\n"
            f"📌 Entry: `{float(signal.entry):.8g}`\n"
            f"🛑 Stop Loss: `{float(signal.stop_loss):.8g}`\n"
            f"✅ TP1: `{float(signal.take_profit_1):.8g}`\n"
        )
        if signal.take_profit_2:
            message += f"✅ TP2: `{float(signal.take_profit_2):.8g}`\n"
        if signal.take_profit_3:
            message += f"✅ TP3: `{float(signal.take_profit_3):.8g}`\n"
        rr_tp1 = _calc_rr(float(signal.entry), float(signal.stop_loss), float(signal.take_profit_1))
        rr_tp2 = _calc_rr(
            float(signal.entry),
            float(signal.stop_loss),
            float(signal.take_profit_2) if signal.take_profit_2 else None,
        )
        if rr_tp1 is not None:
            message += f"\n⚖️ R:R TP1: `1:{float(rr_tp1):.2f}`"
        if rr_tp2 is not None:
            message += f"\n⚖️ R:R TP2: `1:{float(rr_tp2):.2f}`"
        message += "\n"
        message += f"\n🔗 [View on PulseSignal Pro](https://signals.pulsetracker.net)"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                },
            )
            if not response.is_success:
                logger.error(
                    f"Telegram API error: {response.status_code} — {response.text}"
                )

    async def _send_webhook(self, config: AlertConfig, signal: Signal) -> None:
        """POST signal data to the user's webhook URL."""
        if not config.webhook_url:
            return

        payload = {
            "event": "signal.created",
            "signal": {
                "id": str(signal.id),
                "symbol": signal.symbol,
                "direction": signal.direction,
                "timeframe": signal.timeframe,
                "confidence": signal.confidence,
                "entry": float(signal.entry),
                "stop_loss": float(signal.stop_loss),
                "take_profit_1": float(signal.take_profit_1),
                "take_profit_2": float(signal.take_profit_2) if signal.take_profit_2 else None,
                "take_profit_3": float(signal.take_profit_3) if signal.take_profit_3 else None,
                "rr_ratio": float(signal.rr_ratio) if signal.rr_ratio else None,
                "market": signal.market,
                "status": signal.status,
                "fired_at": signal.fired_at.isoformat() if signal.fired_at else None,
            },
        }

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.post(
                    config.webhook_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "PulseSignal-Pro/1.0",
                    },
                )
                if not response.is_success:
                    logger.warning(
                        f"Webhook to {config.webhook_url} returned "
                        f"{response.status_code}"
                    )
            except httpx.RequestError as exc:
                logger.error(f"Webhook delivery failed to {config.webhook_url}: {exc}")

    async def _send_email(self, user: User, signal: Signal) -> None:
        """Send a signal alert by SMTP using owner-configured settings."""
        settings = get_settings()
        async with get_redis() as redis:
            config = await load_system_config(RedisClient(redis))

        if not config.notifications.enable_email_alerts:
            logger.debug("Email alerts disabled in system config.")
            return

        subject, text_body, html_body = build_signal_email(
            symbol=signal.symbol,
            direction=signal.direction,
            timeframe=signal.timeframe,
            confidence=signal.confidence,
            entry=float(signal.entry),
            stop_loss=float(signal.stop_loss),
            take_profit_1=float(signal.take_profit_1),
            dashboard_url=f"{settings.FRONTEND_URL}/dashboard",
        )
        sent = await send_email(
            smtp=config.smtp,
            to_email=user.email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )
        if not sent:
            logger.warning(
                f"Email alert failed or not configured for user {user.email} "
                f"signal={signal.symbol}"
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    async def _get_owned_alert(self, alert_id: UUID, user_id: UUID) -> AlertConfig:
        """Fetch an alert config owned by the user. Raises ValueError if not found."""
        result = await self._db.execute(
            select(AlertConfig).where(
                AlertConfig.id == alert_id,
                AlertConfig.user_id == user_id,
            )
        )
        config = result.scalar_one_or_none()
        if config is None:
            raise ValueError(
                f"AlertConfig {alert_id} not found for user {user_id}."
            )
        return config
