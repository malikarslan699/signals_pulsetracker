from __future__ import annotations

import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from loguru import logger

from app.services.system_config_service import SMTPConfig


def smtp_is_configured(smtp: SMTPConfig) -> bool:
    return bool(
        smtp.enabled
        and smtp.host
        and smtp.port
        and smtp.from_email
    )


def _send_sync(smtp: SMTPConfig, message: EmailMessage) -> None:
    if smtp.use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp.host, smtp.port, context=context, timeout=20) as server:
            if smtp.username:
                server.login(smtp.username, smtp.password)
            server.send_message(message)
        return

    with smtplib.SMTP(smtp.host, smtp.port, timeout=20) as server:
        if smtp.use_tls:
            context = ssl.create_default_context()
            server.starttls(context=context)
        if smtp.username:
            server.login(smtp.username, smtp.password)
        server.send_message(message)


async def send_email(
    smtp: SMTPConfig,
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> bool:
    if not smtp_is_configured(smtp):
        logger.warning("SMTP is not configured; skipping email send.")
        return False

    message = EmailMessage()
    from_name = (smtp.from_name or "PulseSignal Pro").strip()
    message["Subject"] = subject
    message["From"] = f"{from_name} <{smtp.from_email}>"
    message["To"] = to_email
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        await asyncio.to_thread(_send_sync, smtp, message)
        return True
    except Exception as exc:
        logger.error(f"SMTP send failed to {to_email}: {exc}")
        return False


def _check_smtp_sync(smtp: SMTPConfig) -> tuple[bool, str]:
    if smtp.use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp.host, smtp.port, context=context, timeout=15) as server:
            if smtp.username:
                server.login(smtp.username, smtp.password)
        return True, "SMTP SSL connection successful."

    with smtplib.SMTP(smtp.host, smtp.port, timeout=15) as server:
        server.ehlo()
        if smtp.use_tls:
            context = ssl.create_default_context()
            server.starttls(context=context)
            server.ehlo()
        if smtp.username:
            server.login(smtp.username, smtp.password)
    return True, "SMTP connection successful."


async def check_smtp_connection(smtp: SMTPConfig) -> tuple[bool, str]:
    if not smtp_is_configured(smtp):
        return False, "SMTP is not configured."
    try:
        return await asyncio.to_thread(_check_smtp_sync, smtp)
    except Exception as exc:
        return False, f"SMTP check failed: {exc}"


def build_verification_email(verify_url: str) -> tuple[str, str, str]:
    subject = "Verify your PulseSignal Pro email"
    text = (
        "Welcome to PulseSignal Pro.\n\n"
        "Please verify your email by opening this link:\n"
        f"{verify_url}\n\n"
        "If you did not create this account, you can ignore this email."
    )
    html = (
        "<p>Welcome to <b>PulseSignal Pro</b>.</p>"
        "<p>Please verify your email by clicking the link below:</p>"
        f"<p><a href=\"{verify_url}\">{verify_url}</a></p>"
        "<p>If you did not create this account, you can ignore this email.</p>"
    )
    return subject, text, html


def build_signal_email(
    symbol: str,
    direction: str,
    timeframe: str,
    confidence: int,
    entry: float,
    stop_loss: float,
    take_profit_1: float,
    dashboard_url: str,
) -> tuple[str, str, str]:
    subject = f"PulseSignal Alert: {symbol} {direction} ({timeframe})"
    text = (
        f"Signal: {symbol} {direction}\n"
        f"Timeframe: {timeframe}\n"
        f"Confidence: {confidence}%\n"
        f"Entry: {entry:.8g}\n"
        f"Stop Loss: {stop_loss:.8g}\n"
        f"Take Profit 1: {take_profit_1:.8g}\n\n"
        f"Dashboard: {dashboard_url}"
    )
    html = (
        f"<p><b>Signal:</b> {symbol} {direction}</p>"
        f"<p><b>Timeframe:</b> {timeframe}<br/>"
        f"<b>Confidence:</b> {confidence}%<br/>"
        f"<b>Entry:</b> {entry:.8g}<br/>"
        f"<b>Stop Loss:</b> {stop_loss:.8g}<br/>"
        f"<b>Take Profit 1:</b> {take_profit_1:.8g}</p>"
        f"<p><a href=\"{dashboard_url}\">Open Dashboard</a></p>"
    )
    return subject, text, html
