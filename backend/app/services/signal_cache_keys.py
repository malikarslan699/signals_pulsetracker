from __future__ import annotations

from typing import Any


ACTIVE_SIGNAL_SEPARATOR = "|"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def make_active_signal_member(
    symbol: str,
    direction: str,
    timeframe: str,
    signal_id: str,
) -> str:
    return ACTIVE_SIGNAL_SEPARATOR.join(
        [
            _clean(symbol).upper(),
            _clean(direction).upper(),
            _clean(timeframe),
            _clean(signal_id),
        ]
    )


def parse_active_signal_member(member: str) -> dict[str, str | bool | None]:
    raw = _clean(member)
    parts = raw.split(ACTIVE_SIGNAL_SEPARATOR)
    if len(parts) == 4 and all(parts):
        symbol, direction, timeframe, signal_id = parts
        return {
            "member": raw,
            "symbol": symbol,
            "direction": direction,
            "timeframe": timeframe,
            "signal_id": signal_id,
            "is_legacy": False,
        }
    return {
        "member": raw,
        "symbol": raw.upper() if raw else None,
        "direction": None,
        "timeframe": None,
        "signal_id": None,
        "is_legacy": True,
    }


def make_signal_cache_key(
    symbol: str,
    direction: str,
    timeframe: str,
    signal_id: str,
) -> str:
    return f"signal:{make_active_signal_member(symbol, direction, timeframe, signal_id)}"


def make_signal_cache_key_from_member(member: str) -> str:
    return f"signal:{_clean(member)}"


def make_signal_cache_key_from_signal(signal_data: dict[str, Any]) -> str:
    return make_signal_cache_key(
        signal_data.get("symbol", ""),
        signal_data.get("direction", ""),
        signal_data.get("timeframe", ""),
        signal_data.get("id", ""),
    )


def make_legacy_signal_cache_key(symbol: str) -> str:
    return f"signal:{_clean(symbol).upper()}"
