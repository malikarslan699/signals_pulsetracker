from __future__ import annotations

# Canonical lifecycle:
# CREATED -> ARMED -> FILLED -> TP1_REACHED -> TP2_REACHED
#                                       \-> STOPPED
# Any pre/post-fill setup can also end as EXPIRED / INVALIDATED.
#
# Legacy values are still mapped for backward-compatible reads, but new writes
# must use the canonical uppercase lifecycle only.
LEGACY_STATUS_MAP = {
    "active": "FILLED",
    "tp1_hit": "TP1_REACHED",
    "tp2_hit": "TP2_REACHED",
    "tp3_hit": "TP2_REACHED",
    "sl_hit": "STOPPED",
    "expired": "EXPIRED",
    "invalidated": "INVALIDATED",
}

CANONICAL_OPEN_SIGNAL_STATUSES = {"CREATED", "ARMED", "FILLED", "TP1_REACHED"}
CANONICAL_PARTIAL_WIN_SIGNAL_STATUSES = {"TP1_REACHED"}
CANONICAL_WIN_SIGNAL_STATUSES = {"TP2_REACHED"}
CANONICAL_LOSS_SIGNAL_STATUSES = {"STOPPED"}
CANONICAL_STALE_SIGNAL_STATUSES = {"EXPIRED", "INVALIDATED"}

# Compatibility sets used by older DB rows and legacy clients.
OPEN_SIGNAL_STATUSES = CANONICAL_OPEN_SIGNAL_STATUSES | {"active"}
PARTIAL_WIN_SIGNAL_STATUSES = CANONICAL_PARTIAL_WIN_SIGNAL_STATUSES | {"tp1_hit"}
WIN_SIGNAL_STATUSES = CANONICAL_WIN_SIGNAL_STATUSES | {"tp2_hit", "tp3_hit"}
LOSS_SIGNAL_STATUSES = CANONICAL_LOSS_SIGNAL_STATUSES | {"sl_hit"}
STALE_SIGNAL_STATUSES = CANONICAL_STALE_SIGNAL_STATUSES | {"expired", "invalidated"}
FINAL_SIGNAL_STATUSES = WIN_SIGNAL_STATUSES | LOSS_SIGNAL_STATUSES | STALE_SIGNAL_STATUSES

OPEN_STATUS_SQL = "('CREATED','ARMED','FILLED','TP1_REACHED','active')"
PARTIAL_WIN_STATUS_SQL = "('TP1_REACHED','tp1_hit')"
WIN_STATUS_SQL = "('TP2_REACHED','tp2_hit','tp3_hit')"
LOSS_STATUS_SQL = "('STOPPED','sl_hit')"
STALE_STATUS_SQL = "('EXPIRED','INVALIDATED','expired','invalidated')"
FINAL_STATUS_SQL = "('TP2_REACHED','STOPPED','EXPIRED','INVALIDATED','tp2_hit','tp3_hit','sl_hit','expired','invalidated')"
POSITIVE_PROGRESS_STATUS_SQL = "('TP1_REACHED','TP2_REACHED','tp1_hit','tp2_hit','tp3_hit')"


def canonicalize_status(status: str | None) -> str:
    raw = str(status or "").strip()
    return LEGACY_STATUS_MAP.get(raw, raw)


def is_open_status(status: str | None) -> bool:
    return canonicalize_status(status) in CANONICAL_OPEN_SIGNAL_STATUSES


def is_partial_win_status(status: str | None) -> bool:
    return canonicalize_status(status) in CANONICAL_PARTIAL_WIN_SIGNAL_STATUSES


def is_win_status(status: str | None) -> bool:
    return canonicalize_status(status) in CANONICAL_WIN_SIGNAL_STATUSES


def is_loss_status(status: str | None) -> bool:
    return canonicalize_status(status) in CANONICAL_LOSS_SIGNAL_STATUSES


def is_stale_status(status: str | None) -> bool:
    return canonicalize_status(status) in CANONICAL_STALE_SIGNAL_STATUSES


def is_final_status(status: str | None) -> bool:
    return canonicalize_status(status) in (
        CANONICAL_WIN_SIGNAL_STATUSES
        | CANONICAL_LOSS_SIGNAL_STATUSES
        | CANONICAL_STALE_SIGNAL_STATUSES
    )
