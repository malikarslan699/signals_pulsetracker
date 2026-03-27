from __future__ import annotations

from typing import TypedDict

import numpy as np


# ---------------------------------------------------------------------------
# Candle TypedDict
# ---------------------------------------------------------------------------
class Candle(TypedDict):
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: int  # unix milliseconds


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------
def normalize_binance_candle(raw: list) -> Candle:
    """
    Convert a raw Binance kline array to a Candle dict.

    Binance kline format (index → field):
        0  Open time (ms)
        1  Open price
        2  High price
        3  Low price
        4  Close price
        5  Base asset volume
        6  Close time (ms)
        7  Quote asset volume
        …  (remaining fields ignored)
    """
    return Candle(
        timestamp=int(raw[0]),
        open=float(raw[1]),
        high=float(raw[2]),
        low=float(raw[3]),
        close=float(raw[4]),
        volume=float(raw[5]),
    )


def normalize_candles(raw_list: list) -> list[Candle]:
    """Normalize a list of raw Binance kline arrays into Candle dicts."""
    return [normalize_binance_candle(raw) for raw in raw_list]


# ---------------------------------------------------------------------------
# Array conversion helpers
# ---------------------------------------------------------------------------
def candles_to_arrays(
    candles: list[Candle],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert a list of Candle dicts into separate numpy arrays.

    Returns
    -------
    opens, highs, lows, closes, volumes, timestamps  (all dtype=float64
    except timestamps which is int64)
    """
    opens = np.array([c["open"] for c in candles], dtype=np.float64)
    highs = np.array([c["high"] for c in candles], dtype=np.float64)
    lows = np.array([c["low"] for c in candles], dtype=np.float64)
    closes = np.array([c["close"] for c in candles], dtype=np.float64)
    volumes = np.array([c["volume"] for c in candles], dtype=np.float64)
    timestamps = np.array([c["timestamp"] for c in candles], dtype=np.int64)
    return opens, highs, lows, closes, volumes, timestamps


def get_typical_price(
    high: np.ndarray, low: np.ndarray, close: np.ndarray
) -> np.ndarray:
    """Calculate the typical price: (H + L + C) / 3."""
    return (high + low + close) / 3.0


# ---------------------------------------------------------------------------
# Pivot Points
# ---------------------------------------------------------------------------
def calculate_pivot_points(candles: list[Candle]) -> dict:
    """
    Calculate standard pivot points based on the last completed candle.

    Uses the previous period's High, Low, Close to project:
    P, R1, R2, R3, S1, S2, S3.
    """
    if not candles:
        return {}

    prev = candles[-1]
    high = prev["high"]
    low = prev["low"]
    close = prev["close"]

    pivot = (high + low + close) / 3.0
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    r3 = high + 2 * (pivot - low)
    s3 = low - 2 * (high - pivot)

    return {
        "P": round(pivot, 8),
        "R1": round(r1, 8),
        "R2": round(r2, 8),
        "R3": round(r3, 8),
        "S1": round(s1, 8),
        "S2": round(s2, 8),
        "S3": round(s3, 8),
    }


# ---------------------------------------------------------------------------
# Swing High / Low Detection
# ---------------------------------------------------------------------------
def find_swing_highs(highs: np.ndarray, lookback: int = 5) -> list[int]:
    """
    Find indices of swing highs.

    A bar at index i is a swing high if its high is the maximum
    within [i - lookback, i + lookback].
    """
    indices: list[int] = []
    n = len(highs)
    for i in range(lookback, n - lookback):
        window = highs[i - lookback: i + lookback + 1]
        if highs[i] == window.max():
            indices.append(i)
    return indices


def find_swing_lows(lows: np.ndarray, lookback: int = 5) -> list[int]:
    """
    Find indices of swing lows.

    A bar at index i is a swing low if its low is the minimum
    within [i - lookback, i + lookback].
    """
    indices: list[int] = []
    n = len(lows)
    for i in range(lookback, n - lookback):
        window = lows[i - lookback: i + lookback + 1]
        if lows[i] == window.min():
            indices.append(i)
    return indices


# ---------------------------------------------------------------------------
# ATR
# ---------------------------------------------------------------------------
def get_atr(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int = 14,
) -> np.ndarray:
    """
    Calculate the Average True Range (ATR) using Wilder's smoothing.

    Returns an array the same length as inputs (NaN for the first `period` values).
    """
    n = len(closes)
    tr = np.full(n, np.nan)

    for i in range(1, n):
        hl = highs[i] - lows[i]
        hpc = abs(highs[i] - closes[i - 1])
        lpc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hpc, lpc)

    atr = np.full(n, np.nan)
    if n > period:
        # Seed: simple average of first `period` TRs
        atr[period] = np.nanmean(tr[1: period + 1])
        # Wilder's smoothing
        for i in range(period + 1, n):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    return atr


# ---------------------------------------------------------------------------
# Timeframe resampling
# ---------------------------------------------------------------------------
_TF_MINUTES: dict[str, int] = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1H": 60,
    "2H": 120,
    "4H": 240,
    "6H": 360,
    "8H": 480,
    "12H": 720,
    "1D": 1440,
    "1W": 10080,
}


def resample_candles(
    candles: list[Candle],
    from_tf: str,
    to_tf: str,
) -> list[Candle]:
    """
    Resample candles from a lower timeframe to a higher one.

    Parameters
    ----------
    candles : list[Candle]
        Source candles (sorted ascending by timestamp).
    from_tf  : str
        Source timeframe key (e.g. '5m').
    to_tf    : str
        Target timeframe key (e.g. '1H').

    Returns
    -------
    list[Candle]  — resampled candles, empty if not enough data or invalid TFs.
    """
    from_minutes = _TF_MINUTES.get(from_tf)
    to_minutes = _TF_MINUTES.get(to_tf)

    if from_minutes is None or to_minutes is None:
        raise ValueError(f"Unknown timeframe: '{from_tf}' or '{to_tf}'")

    if to_minutes < from_minutes:
        raise ValueError(
            f"Cannot downsample from {from_tf} to {to_tf}: target must be higher."
        )

    ratio = to_minutes // from_minutes
    if ratio == 1:
        return list(candles)

    resampled: list[Candle] = []
    i = 0
    while i + ratio <= len(candles):
        chunk = candles[i: i + ratio]
        resampled.append(
            Candle(
                timestamp=chunk[0]["timestamp"],
                open=chunk[0]["open"],
                high=max(c["high"] for c in chunk),
                low=min(c["low"] for c in chunk),
                close=chunk[-1]["close"],
                volume=sum(c["volume"] for c in chunk),
            )
        )
        i += ratio

    return resampled


# ---------------------------------------------------------------------------
# Support / Resistance helpers
# ---------------------------------------------------------------------------
def find_support_resistance_levels(
    candles: list[Candle],
    lookback: int = 5,
    merge_threshold_pct: float = 0.5,
) -> dict[str, list[float]]:
    """
    Identify key support and resistance price levels from swing points.

    Parameters
    ----------
    candles            : list[Candle]
    lookback           : int   — swing detection lookback window
    merge_threshold_pct: float — merge levels within this % of each other

    Returns
    -------
    dict with keys 'resistance' and 'support', each a sorted list of prices.
    """
    _, highs, lows, closes, _, _ = candles_to_arrays(candles)

    swing_high_idx = find_swing_highs(highs, lookback=lookback)
    swing_low_idx = find_swing_lows(lows, lookback=lookback)

    resistance_levels = sorted({round(highs[i], 8) for i in swing_high_idx})
    support_levels = sorted({round(lows[i], 8) for i in swing_low_idx})

    def _merge(levels: list[float], threshold: float) -> list[float]:
        if not levels:
            return []
        merged: list[float] = [levels[0]]
        for level in levels[1:]:
            if abs(level - merged[-1]) / merged[-1] * 100 <= threshold:
                merged[-1] = (merged[-1] + level) / 2
            else:
                merged.append(level)
        return merged

    return {
        "resistance": _merge(resistance_levels, merge_threshold_pct),
        "support": _merge(support_levels, merge_threshold_pct),
    }
