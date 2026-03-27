from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Set

from fastapi import Depends, HTTPException, status


# ---------------------------------------------------------------------------
# Permission Enum
# ---------------------------------------------------------------------------
class Permission(str, Enum):
    READ_SIGNALS = "read_signals"
    READ_ICT = "read_ict"
    READ_HISTORY = "read_history"
    MANAGE_ALERTS = "manage_alerts"
    ACCESS_SCANNER = "access_scanner"
    ADMIN_PANEL = "admin_panel"
    RESELLER_PANEL = "reseller_panel"
    EXPORT_DATA = "export_data"
    API_ACCESS = "api_access"
    WATCHLIST_UNLIMITED = "watchlist_unlimited"


# ---------------------------------------------------------------------------
# Plan → Permissions mapping
# ---------------------------------------------------------------------------
PLAN_PERMISSIONS: Dict[str, Set[Permission]] = {
    "trial": {
        Permission.READ_SIGNALS,
        Permission.READ_ICT,
        Permission.READ_HISTORY,
    },
    "monthly": {
        Permission.READ_SIGNALS,
        Permission.READ_ICT,
        Permission.READ_HISTORY,
        Permission.MANAGE_ALERTS,
        Permission.ACCESS_SCANNER,
        Permission.EXPORT_DATA,
        Permission.API_ACCESS,
    },
    "yearly": {
        Permission.READ_SIGNALS,
        Permission.READ_ICT,
        Permission.READ_HISTORY,
        Permission.MANAGE_ALERTS,
        Permission.ACCESS_SCANNER,
        Permission.EXPORT_DATA,
        Permission.API_ACCESS,
    },
    "lifetime": {
        Permission.READ_SIGNALS,
        Permission.READ_ICT,
        Permission.READ_HISTORY,
        Permission.MANAGE_ALERTS,
        Permission.ACCESS_SCANNER,
        Permission.EXPORT_DATA,
        Permission.API_ACCESS,
        Permission.WATCHLIST_UNLIMITED,
    },
}

# Role overrides: admin/reseller get additional permissions on top of their plan
ROLE_EXTRA_PERMISSIONS: Dict[str, Set[Permission]] = {
    "admin": {
        Permission.ADMIN_PANEL,
        Permission.ACCESS_SCANNER,
        Permission.EXPORT_DATA,
        Permission.API_ACCESS,
        Permission.WATCHLIST_UNLIMITED,
    },
    "owner": {
        Permission.ADMIN_PANEL,
        Permission.ACCESS_SCANNER,
        Permission.EXPORT_DATA,
        Permission.API_ACCESS,
        Permission.WATCHLIST_UNLIMITED,
    },
    "superadmin": {
        Permission.ADMIN_PANEL,
        Permission.ACCESS_SCANNER,
        Permission.EXPORT_DATA,
        Permission.API_ACCESS,
        Permission.WATCHLIST_UNLIMITED,
    },
    "reseller": {
        Permission.RESELLER_PANEL,
        Permission.MANAGE_ALERTS,
    },
}


def has_permission(user, permission: Permission) -> bool:
    """
    Return True if the user (ORM model) holds the given permission.

    Checks plan-based permissions first, then adds role-based extras.
    """
    from datetime import datetime, timezone

    plan = getattr(user, "plan", "trial") or "trial"
    role = getattr(user, "role", "user") or "user"

    # Check subscription expiry for time-limited plans
    if plan in ("monthly", "yearly", "trial"):
        plan_expires_at = getattr(user, "plan_expires_at", None)
        if plan_expires_at is not None:
            now = datetime.now(tz=timezone.utc)
            expires = plan_expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < now:
                plan = "trial"

    allowed: Set[Permission] = PLAN_PERMISSIONS.get(plan, set()).copy()

    # Merge role extras
    extra = ROLE_EXTRA_PERMISSIONS.get(role, set())
    allowed |= extra

    return permission in allowed


def require_permission(permission: Permission):
    """
    Dependency factory that enforces a specific permission.

    Usage::

        @router.get("/ict", dependencies=[Depends(require_permission(Permission.READ_ICT))])
    """
    from app.core.auth import get_current_active_user

    async def _check_permission(current_user=Depends(get_current_active_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Permission denied: '{permission.value}' requires a "
                    "higher subscription plan."
                ),
            )
        return current_user

    return _check_permission


# ---------------------------------------------------------------------------
# Plan Limits
# ---------------------------------------------------------------------------
@dataclass
class PlanLimits:
    """Quantitative limits for a subscription plan."""

    max_pairs_watchlist: int
    max_alerts: int
    history_days: int
    max_api_calls_per_min: int
    can_export: bool = False
    can_use_websocket: bool = False
    max_concurrent_ws: int = 0
    signals_per_day: int = 0  # 0 = unlimited


PLAN_LIMITS: Dict[str, PlanLimits] = {
    "trial": PlanLimits(
        max_pairs_watchlist=10,
        max_alerts=0,
        history_days=7,
        max_api_calls_per_min=30,
        can_export=False,
        can_use_websocket=False,
        max_concurrent_ws=0,
        signals_per_day=20,
    ),
    "monthly": PlanLimits(
        max_pairs_watchlist=100,
        max_alerts=10,
        history_days=90,
        max_api_calls_per_min=300,
        can_export=True,
        can_use_websocket=True,
        max_concurrent_ws=3,
        signals_per_day=0,
    ),
    "yearly": PlanLimits(
        max_pairs_watchlist=250,
        max_alerts=20,
        history_days=180,
        max_api_calls_per_min=600,
        can_export=True,
        can_use_websocket=True,
        max_concurrent_ws=5,
        signals_per_day=0,
    ),
    "lifetime": PlanLimits(
        max_pairs_watchlist=0,  # 0 = unlimited
        max_alerts=0,           # unlimited
        history_days=365,
        max_api_calls_per_min=1000,
        can_export=True,
        can_use_websocket=True,
        max_concurrent_ws=10,
        signals_per_day=0,
    ),
}

# Alias so any legacy "free" lookup falls back to trial limits
PLAN_LIMITS["free"] = PLAN_LIMITS["trial"]


def get_plan_limits(plan: str) -> PlanLimits:
    """Return the PlanLimits for the given plan string (falls back to trial)."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["trial"])
