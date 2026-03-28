from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.auth import get_current_active_user
from app.core.exceptions import ValidationError
from app.database import get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.redis_client import RedisClient, get_redis_client
from app.services.package_config_service import load_packages_config, packages_to_plans_list

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])
settings = get_settings()

# ---------------------------------------------------------------------------
# Plan definitions
# ---------------------------------------------------------------------------
PLANS = {
    "trial": {
        "id": "trial",
        "name": "Trial",
        "price_usd": 0,
        "duration_days": 30,
        "duration_label": "30 days",
        "badge_text": "",
        "badge_color": "#6B7280",
        "features": [
            "Delayed signals",
            "Signal history (7 days)",
            "Crypto market access",
            "Up to 10 watchlist pairs",
            "20 signals/day",
        ],
        "stripe_price_id": None,
    },
    "monthly": {
        "id": "monthly",
        "name": "Monthly Pro",
        "price_usd": 29,
        "duration_days": 30,
        "duration_label": "/ month",
        "badge_text": "Most Popular",
        "badge_color": "#8B5CF6",
        "features": [
            "Real-time signals",
            "Signal history (90 days)",
            "Crypto + Forex markets",
            "Telegram alerts",
            "ICT & indicator breakdown",
            "Up to 10 alert configs",
            "Data export & API access",
            "Up to 3 WebSocket connections",
        ],
        "stripe_price_id": settings.STRIPE_MONTHLY_PRICE_ID or None,
    },
    "yearly": {
        "id": "yearly",
        "name": "Yearly Pro",
        "price_usd": 199,
        "duration_days": 365,
        "duration_label": "/ year",
        "badge_text": "Save 43%",
        "badge_color": "#10B981",
        "features": [
            "Everything in Monthly Pro",
            "Signal history (180 days)",
            "Up to 20 alert configs",
            "Up to 250 watchlist pairs",
            "Up to 5 WebSocket connections",
            "Priority support",
        ],
        "stripe_price_id": None,
    },
    "lifetime": {
        "id": "lifetime",
        "name": "Lifetime Pro",
        "price_usd": 299,
        "duration_days": None,  # Never expires
        "duration_label": "one-time",
        "badge_text": "Best Value",
        "badge_color": "#F59E0B",
        "features": [
            "Everything in Yearly Pro",
            "Lifetime access — no recurring fees",
            "Unlimited watchlist & alerts",
            "365-day signal history",
            "Up to 10 WebSocket connections",
            "Priority support",
        ],
        "stripe_price_id": settings.STRIPE_LIFETIME_PRICE_ID or None,
    },
}


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------
class CheckoutRequest(BaseModel):
    plan: str  # monthly | lifetime
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class SubscriptionResponse(BaseModel):
    id: str
    plan: str
    status: str
    price: float
    currency: str
    started_at: datetime
    expires_at: Optional[datetime] = None
    stripe_subscription_id: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
async def _activate_subscription(
    db: AsyncSession,
    user: User,
    plan: str,
    stripe_subscription_id: Optional[str] = None,
    stripe_customer_id: Optional[str] = None,
    stripe_payment_intent_id: Optional[str] = None,
) -> Subscription:
    """
    Activate a subscription for the user.
    Updates user.plan and user.plan_expires_at. Creates a Subscription record.
    """
    price_map = {"monthly": 29.00, "yearly": 199.00, "lifetime": 299.00}
    price = price_map.get(plan, 0.00)

    now = datetime.now(tz=timezone.utc)
    expires_at: Optional[datetime] = None

    if plan == "monthly":
        expires_at = now + timedelta(days=30)
    elif plan == "yearly":
        expires_at = now + timedelta(days=365)
    elif plan == "lifetime":
        expires_at = None  # never expires

    # Deactivate any existing active subscriptions
    existing_result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .where(Subscription.status == "active")
    )
    for sub in existing_result.scalars().all():
        sub.status = "cancelled"
        sub.cancelled_at = now

    # Update user record
    user.plan = plan
    user.plan_expires_at = expires_at

    # Create new subscription record
    subscription = Subscription(
        user_id=user.id,
        plan=plan,
        price=price,
        currency="USD",
        stripe_subscription_id=stripe_subscription_id,
        stripe_customer_id=stripe_customer_id,
        stripe_payment_intent_id=stripe_payment_intent_id,
        status="active",
        started_at=now,
        expires_at=expires_at,
    )
    db.add(subscription)
    await db.flush()

    logger.info(
        f"Subscription activated: user={user.id} plan={plan} "
        f"stripe_sub={stripe_subscription_id}"
    )
    return subscription


async def _handle_subscription_cancelled(
    db: AsyncSession,
    stripe_subscription_id: str,
) -> None:
    """
    Handle Stripe subscription.deleted event.
    Marks the subscription as cancelled and downgrades the user to free.
    """
    result = await db.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription_id
        )
    )
    subscription: Optional[Subscription] = result.scalar_one_or_none()

    if subscription is None:
        logger.warning(
            f"Stripe cancellation for unknown subscription: {stripe_subscription_id}"
        )
        return

    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.now(tz=timezone.utc)

    # Downgrade user to free plan
    user_result = await db.execute(
        select(User).where(User.id == subscription.user_id)
    )
    user: Optional[User] = user_result.scalar_one_or_none()
    if user:
        user.plan = "trial"
        user.plan_expires_at = None
        logger.info(
            f"User {user.id} downgraded to trial (Stripe sub {stripe_subscription_id} cancelled)."
        )

    await db.flush()


# ---------------------------------------------------------------------------
# GET /plans
# ---------------------------------------------------------------------------
@router.get(
    "/plans",
    summary="Return available subscription plans",
)
async def list_plans(redis: RedisClient = Depends(get_redis_client)) -> dict:
    """Return the available subscription plans and their pricing (admin-editable)."""
    try:
        config = await load_packages_config(redis)
        plans = packages_to_plans_list(config)
        if plans:
            return {"plans": plans}
    except Exception:
        pass
    # Fallback to static PLANS dict
    return {"plans": list(PLANS.values())}


# ---------------------------------------------------------------------------
# POST /checkout
# ---------------------------------------------------------------------------
@router.post(
    "/checkout",
    summary="Create a Stripe checkout session",
)
async def create_checkout_session(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create a Stripe Checkout Session for the requested plan.
    Returns the session URL to redirect the user to.
    """
    if payload.plan not in ("monthly", "yearly", "lifetime"):
        raise ValidationError(f"Invalid plan '{payload.plan}'. Choose 'monthly', 'yearly', or 'lifetime'.")

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment processing is not configured.",
        )

    plan_info = PLANS[payload.plan]
    price_id = plan_info.get("stripe_price_id")
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Stripe price ID for '{payload.plan}' plan is not configured.",
        )

    try:
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY

        success_url = payload.success_url or f"{settings.FRONTEND_URL}/dashboard?payment=success"
        cancel_url = payload.cancel_url or f"{settings.FRONTEND_URL}/pricing?payment=cancelled"

        session_params: dict = {
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": "subscription" if payload.plan in ("monthly", "yearly") else "payment",
            "success_url": success_url + "&session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": cancel_url,
            "client_reference_id": str(current_user.id),
            "customer_email": current_user.email,
            "metadata": {
                "user_id": str(current_user.id),
                "plan": payload.plan,
            },
        }

        session = stripe.checkout.Session.create(**session_params)

        logger.info(
            f"Stripe checkout session created: user={current_user.id} "
            f"plan={payload.plan} session={session.id}"
        )

        return {
            "url": session.url,  # backward-compatible key for older frontend code
            "checkout_url": session.url,
            "session_id": session.id,
            "plan": payload.plan,
        }

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe SDK is not installed.",
        )
    except Exception as exc:
        logger.error(f"Stripe checkout error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not create checkout session. Please try again.",
        )


# ---------------------------------------------------------------------------
# POST /webhook
# ---------------------------------------------------------------------------
@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Handle Stripe webhook events",
    include_in_schema=False,  # Hidden from public docs for security
)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Process Stripe webhook events:
    - checkout.session.completed → activate subscription
    - customer.subscription.deleted → cancel subscription
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment processing is not configured.",
        )

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        payload_bytes = await request.body()
        sig_header = request.headers.get("stripe-signature", "")

        if settings.STRIPE_WEBHOOK_SECRET:
            try:
                event = stripe.Webhook.construct_event(
                    payload_bytes, sig_header, settings.STRIPE_WEBHOOK_SECRET
                )
            except stripe.error.SignatureVerificationError:
                logger.warning("Stripe webhook signature verification failed.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid webhook signature.",
                )
        else:
            # No webhook secret configured — parse event directly (dev mode)
            event = stripe.Event.construct_from(
                json.loads(payload_bytes), stripe.api_key
            )

        event_type = event["type"]
        event_data = event["data"]["object"]

        logger.info(f"Stripe webhook received: {event_type}")

        if event_type == "checkout.session.completed":
            user_id = event_data.get("client_reference_id") or (
                event_data.get("metadata") or {}
            ).get("user_id")
            plan = (event_data.get("metadata") or {}).get("plan", "monthly")
            stripe_sub_id = event_data.get("subscription")
            stripe_customer_id = event_data.get("customer")
            stripe_payment_intent = event_data.get("payment_intent")

            if user_id:
                from uuid import UUID

                result = await db.execute(
                    select(User).where(User.id == UUID(user_id))
                )
                user: Optional[User] = result.scalar_one_or_none()
                if user:
                    await _activate_subscription(
                        db=db,
                        user=user,
                        plan=plan,
                        stripe_subscription_id=stripe_sub_id,
                        stripe_customer_id=stripe_customer_id,
                        stripe_payment_intent_id=stripe_payment_intent,
                    )
                else:
                    logger.error(f"Stripe webhook: user {user_id} not found.")
            else:
                logger.error("Stripe webhook: missing client_reference_id.")

        elif event_type in ("customer.subscription.deleted", "subscription.deleted"):
            stripe_sub_id = event_data.get("id")
            if stripe_sub_id:
                await _handle_subscription_cancelled(db, stripe_sub_id)

        else:
            logger.debug(f"Unhandled Stripe event type: {event_type}")

        return {"received": True}

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe SDK is not installed.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Stripe webhook processing error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed.",
        )


# ---------------------------------------------------------------------------
# GET /my
# ---------------------------------------------------------------------------
@router.get(
    "/my",
    summary="Get the current user's active subscription",
)
async def my_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the current user's active subscription details."""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == "active")
        .order_by(Subscription.started_at.desc())
        .limit(1)
    )
    subscription: Optional[Subscription] = result.scalar_one_or_none()

    if subscription is None:
        return {
            "has_subscription": False,
            "plan": current_user.plan,
            "plan_expires_at": (
                current_user.plan_expires_at.isoformat()
                if current_user.plan_expires_at
                else None
            ),
            "subscription": None,
        }

    return {
        "has_subscription": True,
        "plan": current_user.plan,
        "plan_expires_at": (
            current_user.plan_expires_at.isoformat()
            if current_user.plan_expires_at
            else None
        ),
        "subscription": {
            "id": str(subscription.id),
            "plan": subscription.plan,
            "status": subscription.status,
            "price": float(subscription.price),
            "currency": subscription.currency,
            "started_at": subscription.started_at.isoformat(),
            "expires_at": (
                subscription.expires_at.isoformat() if subscription.expires_at else None
            ),
            "stripe_subscription_id": subscription.stripe_subscription_id,
        },
    }


# ---------------------------------------------------------------------------
# POST /crypto-payment — User submits crypto TxID, owner gets email alert
# ---------------------------------------------------------------------------
class CryptoPaymentRequest(BaseModel):
    plan: str       # monthly | yearly | lifetime
    txid: str       # Transaction ID / hash
    network: str    # BTC | ETH | USDT-TRC20 | USDT-ERC20 | BNB
    amount_usd: float


@router.post("/crypto-payment", summary="Submit crypto payment TxID for manual verification")
async def submit_crypto_payment(
    payload: CryptoPaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    """
    User submits their crypto transaction ID after paying.
    System stores it as pending and emails owner for manual confirmation.
    Owner then upgrades user plan via admin panel.
    """
    if payload.plan not in ("monthly", "yearly", "lifetime"):
        raise ValidationError("Invalid plan. Must be monthly, yearly, or lifetime.")

    if not payload.txid or len(payload.txid) < 10:
        raise ValidationError("Invalid transaction ID.")

    price_map = {"monthly": 29, "yearly": 199, "lifetime": 299}
    expected_price = price_map[payload.plan]

    # Store pending request in Redis (expires in 7 days)
    import json
    from datetime import datetime, timezone
    request_data = {
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "username": current_user.username,
        "plan": payload.plan,
        "txid": payload.txid,
        "network": payload.network,
        "amount_usd": payload.amount_usd,
        "expected_usd": expected_price,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    }
    redis_key = f"crypto:payment:{current_user.id}:{payload.plan}"
    await redis.client.set(redis_key, json.dumps(request_data), ex=604800)  # 7 days

    # Add to pending list
    await redis.client.lpush("crypto:payments:pending", redis_key)

    # Send email notification to owner
    try:
        from app.services.mailer import send_email, smtp_is_configured
        config_svc = settings
        # Load SMTP from system config stored in Redis/DB
        import os
        smtp_host = os.getenv("SMTP_HOST", "")
        smtp_from = os.getenv("SMTP_FROM_EMAIL", "")
        if smtp_host and smtp_from:
            from app.services.system_config_service import SMTPConfig
            smtp = SMTPConfig(
                enabled=True,
                host=smtp_host,
                port=int(os.getenv("SMTP_PORT", "465")),
                username=os.getenv("SMTP_USERNAME", ""),
                password=os.getenv("SMTP_PASSWORD", ""),
                from_email=smtp_from,
                from_name=os.getenv("SMTP_FROM_NAME", "PulseSignal Pro"),
                use_tls=os.getenv("SMTP_USE_TLS", "false").lower() == "true",
                use_ssl=os.getenv("SMTP_USE_SSL", "true").lower() == "true",
            )
            subject = f"[PulseSignal] Crypto Payment — {current_user.email} → {payload.plan}"
            body = (
                f"A new crypto payment requires verification.\n\n"
                f"User: {current_user.username} ({current_user.email})\n"
                f"Plan: {payload.plan.upper()} (${expected_price} USD)\n"
                f"Network: {payload.network}\n"
                f"TxID: {payload.txid}\n"
                f"Amount claimed: ${payload.amount_usd}\n"
                f"Submitted: {request_data['submitted_at']}\n\n"
                f"ACTION: Verify on blockchain explorer, then go to Admin → Users → set plan to {payload.plan}."
            )
            await send_email(smtp, to_email=smtp_from, subject=subject, text_body=body)
    except Exception as e:
        logger.warning(f"Could not send owner email for crypto payment: {e}")

    logger.info(
        f"Crypto payment submitted: user={current_user.id} plan={payload.plan} "
        f"txid={payload.txid} network={payload.network}"
    )

    return {
        "status": "pending",
        "message": "Payment submitted. Our team will verify your transaction within 24 hours and activate your plan.",
        "plan": payload.plan,
        "txid": payload.txid,
        "network": payload.network,
    }


@router.get("/crypto-payment/my-pending", summary="Check user's pending crypto payment")
async def get_my_crypto_payment(
    current_user: User = Depends(get_current_active_user),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    import json
    for plan in ("monthly", "yearly", "lifetime"):
        redis_key = f"crypto:payment:{current_user.id}:{plan}"
        raw = await redis.client.get(redis_key)
        if raw:
            data = json.loads(raw)
            return {"has_pending": True, "payment": data}
    return {"has_pending": False, "payment": None}
