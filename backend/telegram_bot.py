"""
PulseSignal Pro — Telegram Bot
Handles user authentication and signal delivery

Commands:
/start [code]  — Start bot, optionally link account
/signals       — Latest 5 signals
/stats         — Platform statistics
/subscribe     — Subscription info
/help          — Help message
/setfilters    — Configure alert filters
/mystatus      — Show user's plan and alert status
"""
import asyncio
import os
import json
import logging
import uuid
from datetime import datetime, timezone

import redis
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Config
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://signals.pulsetracker.net")
DB_URL = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis client
r = redis.from_url(REDIS_URL)


def get_db_user(telegram_chat_id: int):
    """Look up user by telegram_chat_id"""
    if not DB_URL:
        return None
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, username, email, plan, is_active FROM users WHERE telegram_chat_id = :cid"),
                {"cid": telegram_chat_id}
            ).fetchone()
            return dict(row._mapping) if row else None
    except Exception as e:
        logger.error(f"DB lookup error: {e}")
        return None


def _link_user_with_code(code: str, chat_id: int, telegram_username: str | None = None):
    """
    Link Telegram chat_id to an existing app user using a verification code
    created by POST /api/v1/auth/connect-telegram.
    """
    if not DB_URL:
        return False, "Database is not configured on bot service."

    redis_key = f"telegram:verify:{code}"
    user_id_raw = r.get(redis_key)
    if not user_id_raw:
        return False, "Code invalid or expired. Generate a new code from Settings."

    if isinstance(user_id_raw, (bytes, bytearray)):
        user_id_raw = user_id_raw.decode("utf-8", errors="ignore")

    try:
        user_id = str(uuid.UUID(str(user_id_raw)))
    except Exception:
        # Corrupt or legacy value
        return False, "Verification code is malformed. Generate a new one."

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(DB_URL)
        with engine.begin() as conn:
            # If this chat was linked to another user previously, detach it first.
            conn.execute(
                text(
                    "UPDATE users SET telegram_chat_id = NULL "
                    "WHERE telegram_chat_id = :cid AND id::text <> :uid"
                ),
                {"cid": chat_id, "uid": user_id},
            )

            row = conn.execute(
                text(
                    """
                    UPDATE users
                    SET telegram_chat_id = :cid,
                        telegram_username = COALESCE(:uname, telegram_username),
                        is_verified = TRUE
                    WHERE id::text = :uid
                    RETURNING username
                    """
                ),
                {"cid": chat_id, "uid": user_id, "uname": telegram_username},
            ).fetchone()

        # Invalidate code after processing.
        r.delete(redis_key)

        if not row:
            return False, "User not found for this code. Generate a new code."

        username = row._mapping.get("username") or "Trader"
        return True, f"Telegram linked successfully with @{telegram_username or 'your account'} ({username})."
    except Exception as e:
        logger.error(f"Telegram link error: {e}")
        return False, "Link failed due to a server error. Please try again."


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    chat_id = update.effective_chat.id
    args = context.args

    # If called with a verification code, link Telegram to app account
    if args:
        code = args[0].strip().upper()
        tg_username = update.effective_user.username if update.effective_user else None
        ok, msg = _link_user_with_code(code, chat_id, tg_username)
        if ok:
            await update.message.reply_html(
                "✅ <b>Telegram linked successfully!</b>\n\n"
                f"{msg}\n\n"
                f"🔗 {FRONTEND_URL}/settings",
                disable_web_page_preview=True,
            )
        else:
            await update.message.reply_html(
                "❌ <b>Could not verify code</b>\n\n"
                f"{msg}\n\n"
                f"Generate a new code from: {FRONTEND_URL}/settings",
                disable_web_page_preview=True,
            )
        return

    # Check if user is linked
    user = get_db_user(chat_id)

    if user:
        plan_label = {
            "trial": "Trial",
            "monthly": "Monthly Pro",
            "yearly": "Yearly Pro",
            "lifetime": "Lifetime Pro",
        }.get(user.get("plan", "trial"), "Trial")

        keyboard = [
            [InlineKeyboardButton("📊 Latest Signals", callback_data="signals")],
            [InlineKeyboardButton("📈 Platform Stats", callback_data="stats")],
            [InlineKeyboardButton("⚙️ My Alerts", callback_data="my_alerts")],
            [InlineKeyboardButton("🔗 Open Dashboard", url=f"{FRONTEND_URL}/dashboard")],
        ]

        await update.message.reply_html(
            f"👋 <b>Welcome back, {user.get('username', 'Trader')}!</b>\n\n"
            f"📊 Plan: <b>{plan_label}</b>\n\n"
            "Choose an option below:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🚀 Create Account", url=f"{FRONTEND_URL}/register")],
            [InlineKeyboardButton("🔑 Login", url=f"{FRONTEND_URL}/login")],
        ]

        await update.message.reply_html(
            "🔥 <b>Welcome to PulseSignal Pro!</b>\n\n"
            "Professional trading signals powered by:\n"
            "✅ ICT Smart Money concepts\n"
            "✅ 35+ technical indicators\n"
            "✅ 500+ crypto + forex pairs\n"
            "✅ Real-time Telegram alerts\n\n"
            "Get started at:\n"
            f"🔗 {FRONTEND_URL}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True,
        )


async def cmd_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show latest 5 signals"""
    chat_id = update.effective_chat.id
    user = get_db_user(chat_id)

    if not user:
        await update.message.reply_text(
            "Please create an account first:\n"
            f"🔗 {FRONTEND_URL}/register"
        )
        return

    # Get signals from Redis
    try:
        active_raw = r.zrevrange("signals:active", 0, 4, withscores=True)

        if not active_raw:
            await update.message.reply_text("No active signals right now. Check back soon!")
            return

        msg = "📊 <b>Latest Signals — PulseSignal Pro</b>\n\n"

        for raw, score in active_raw:
            try:
                sig = json.loads(raw)
                direction = sig.get("direction", "")
                symbol = sig.get("symbol", "")
                tf = sig.get("timeframe", "")
                conf = sig.get("confidence", 0)
                entry = sig.get("entry", 0)

                emoji = "🟢" if direction == "LONG" else "🔴"
                arrow = "▲" if direction == "LONG" else "▼"

                fired_at = sig.get("fired_at", "")
                try:
                    dt = datetime.fromisoformat(fired_at.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M UTC")
                except Exception:
                    time_str = "—"

                msg += f"{emoji} <b>{symbol}</b> {direction} {arrow} | {tf} | {conf}/100 | ${entry:,.4g} | {time_str}\n"
            except Exception:
                pass

        plan = user.get("plan", "trial")
        if plan == "trial":
            msg += f"\n⭐ <i>Upgrade to Pro for full details + alerts</i>\n{FRONTEND_URL}/pricing"
        else:
            msg += f"\n🔗 <a href='{FRONTEND_URL}/dashboard'>View Full Dashboard</a>"

        await update.message.reply_html(msg, disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"cmd_signals error: {e}")
        await update.message.reply_text("Error fetching signals. Try again shortly.")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show platform statistics"""
    try:
        cached = r.get("analytics:win_rates")
        if cached:
            stats = json.loads(cached)
            win_rate = stats.get("win_rate", 0)
            total = stats.get("total_signals", 0)
            by_dir = stats.get("by_direction", {})
            long_wr = by_dir.get("LONG", {}).get("win_rate", 0)
            short_wr = by_dir.get("SHORT", {}).get("win_rate", 0)

            msg = (
                "📈 <b>PulseSignal Pro — Stats</b>\n\n"
                f"🎯 Overall Win Rate: <b>{win_rate}%</b>\n"
                f"📊 Total Signals: <b>{total}</b>\n"
                f"🟢 Long Win Rate: <b>{long_wr}%</b>\n"
                f"🔴 Short Win Rate: <b>{short_wr}%</b>\n\n"
                f"🔗 {FRONTEND_URL}/stats"
            )
        else:
            msg = (
                "📈 <b>PulseSignal Pro</b>\n\n"
                "✅ 500+ pairs monitored\n"
                "✅ 35+ indicators + ICT\n"
                "✅ Scanning every 10 minutes\n\n"
                f"🔗 {FRONTEND_URL}"
            )

        await update.message.reply_html(msg, disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"cmd_stats error: {e}")
        await update.message.reply_text("Stats temporarily unavailable.")


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscription info"""
    keyboard = [
        [InlineKeyboardButton("⭐ Pro Monthly — $29/mo", url=f"{FRONTEND_URL}/pricing")],
        [InlineKeyboardButton("💎 Lifetime — $149 once", url=f"{FRONTEND_URL}/pricing")],
    ]

    await update.message.reply_html(
        "💰 <b>PulseSignal Pro Plans</b>\n\n"
        "🆓 <b>Free Trial</b> — 24 hours\n"
        "   • 5 signal previews\n"
        "   • No alerts\n\n"
        "⭐ <b>Pro Monthly</b> — $29/month\n"
        "   • Unlimited signals\n"
        "   • 500+ pairs\n"
        "   • Telegram alerts\n"
        "   • ICT breakdown\n\n"
        "💎 <b>Lifetime Pro</b> — $149 once\n"
        "   • Everything in Pro\n"
        "   • Forever access\n"
        "   • API access\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cmd_mystatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's current status"""
    chat_id = update.effective_chat.id
    user = get_db_user(chat_id)

    if not user:
        await update.message.reply_text(
            "Your Telegram is not linked to a PulseSignal Pro account.\n"
            f"Register at: {FRONTEND_URL}/register"
        )
        return

    plan = user.get("plan", "trial")
    plan_labels = {
        "trial": "Trial",
        "monthly": "Monthly Pro",
        "yearly": "Yearly Pro",
        "lifetime": "Lifetime Pro",
    }

    msg = (
        f"👤 <b>Your Account Status</b>\n\n"
        f"Username: <b>{user.get('username', '—')}</b>\n"
        f"Plan: <b>{plan_labels.get(plan, plan)}</b>\n"
        f"Alerts: <b>{'✅ Active' if plan in ('monthly', 'yearly', 'lifetime') else '❌ Requires upgrade'}</b>\n\n"
        f"🔗 {FRONTEND_URL}/settings"
    )

    await update.message.reply_html(msg, disable_web_page_preview=True)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    await update.message.reply_html(
        "🤖 <b>PulseSignal Pro Bot Commands</b>\n\n"
        "/start — Welcome & account link\n"
        "/signals — Latest 5 trading signals\n"
        "/stats — Platform performance stats\n"
        "/subscribe — View subscription plans\n"
        "/mystatus — Your account & plan info\n"
        "/help — This message\n\n"
        f"🔗 Dashboard: {FRONTEND_URL}/dashboard\n\n"
        "<i>⚠️ Signals are not financial advice. Always DYOR.</i>",
        disable_web_page_preview=True,
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "signals":
        # Simulate the signals command
        update.message = query.message
        await cmd_signals(update, context)
    elif data == "stats":
        update.message = query.message
        await cmd_stats(update, context)
    elif data == "my_alerts":
        await query.edit_message_text(
            "⚙️ Configure your alerts at:\n"
            f"🔗 {FRONTEND_URL}/alerts",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Open Alert Settings", url=f"{FRONTEND_URL}/alerts")]
            ])
        )


def main():
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return

    logger.info("Starting PulseSignal Pro Telegram Bot...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("signals", cmd_signals))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("mystatus", cmd_mystatus))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
