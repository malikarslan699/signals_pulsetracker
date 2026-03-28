from __future__ import annotations

OPEN_SIGNAL_STATUSES = {"active", "CREATED", "ARMED", "FILLED"}
WIN_SIGNAL_STATUSES = {"tp1_hit", "tp2_hit", "tp3_hit", "TP1_REACHED", "TP2_REACHED"}
LOSS_SIGNAL_STATUSES = {"sl_hit", "STOPPED"}
STALE_SIGNAL_STATUSES = {"expired", "invalidated", "EXPIRED", "INVALIDATED"}
FINAL_SIGNAL_STATUSES = WIN_SIGNAL_STATUSES | LOSS_SIGNAL_STATUSES | STALE_SIGNAL_STATUSES


def is_open_status(status: str | None) -> bool:
    return str(status or "") in OPEN_SIGNAL_STATUSES


def is_win_status(status: str | None) -> bool:
    return str(status or "") in WIN_SIGNAL_STATUSES


def is_loss_status(status: str | None) -> bool:
    return str(status or "") in LOSS_SIGNAL_STATUSES


def is_stale_status(status: str | None) -> bool:
    return str(status or "") in STALE_SIGNAL_STATUSES


def is_final_status(status: str | None) -> bool:
    return str(status or "") in FINAL_SIGNAL_STATUSES
