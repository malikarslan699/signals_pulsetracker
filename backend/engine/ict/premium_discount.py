"""
ICT Premium & Discount Arrays — PulseSignal Pro

Core ICT concept:
- Find the current trading range (swing high to swing low)
- Above 50% of range = PREMIUM  (sell zone, look for shorts)
- Below 50% of range = DISCOUNT (buy zone, look for longs)
- At 50%             = EQUILIBRIUM (neutral)

Key Fibonacci levels within the range:
- 0.0   = Swing Low  (maximum discount)
- 0.236 = Deep discount
- 0.382 = Discount zone top
- 0.5   = Equilibrium
- 0.618 = Premium zone bottom
- 0.786 = Deep premium
- 1.0   = Swing High (maximum premium)
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class PremiumDiscountResult:
    swing_high: float
    swing_low: float
    equilibrium: float          # 50% of range
    current_pct: float          # 0.0-1.0, where current price sits in range
    zone: str                   # 'deep_discount','discount','equilibrium','premium','deep_premium'
    is_discount: bool           # True if below 0.5
    is_premium: bool            # True if above 0.5
    discount_top: float         # 0.382 level (top of discount zone)
    premium_bottom: float       # 0.618 level (bottom of premium zone)
    fib_236: float
    fib_382: float
    fib_500: float
    fib_618: float
    fib_786: float
    score_long: int             # bonus for longs in discount
    score_short: int            # bonus for shorts in premium


def _find_swing_high(highs: np.ndarray, window: int = 3) -> float:
    """Find the most significant swing high over the array."""
    n = len(highs)
    candidates = []
    for i in range(window, n - window):
        if all(highs[i] >= highs[i - k] for k in range(1, window + 1)) and \
           all(highs[i] >= highs[i + k] for k in range(1, window + 1)):
            candidates.append(float(highs[i]))
    if candidates:
        return max(candidates)
    return float(np.max(highs))


def _find_swing_low(lows: np.ndarray, window: int = 3) -> float:
    """Find the most significant swing low over the array."""
    n = len(lows)
    candidates = []
    for i in range(window, n - window):
        if all(lows[i] <= lows[i - k] for k in range(1, window + 1)) and \
           all(lows[i] <= lows[i + k] for k in range(1, window + 1)):
            candidates.append(float(lows[i]))
    if candidates:
        return min(candidates)
    return float(np.min(lows))


def analyze_premium_discount(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    lookback: int = 50,
) -> PremiumDiscountResult:
    """
    Determine where the current price sits within the most recent
    significant swing high/low range.

    Steps:
    1. Extract the last `lookback` candles.
    2. Find the dominant swing high and swing low using pivot detection
       with a 3-bar window.  Falls back to simple max/min if no pivots found.
    3. Compute Fibonacci levels across the range.
    4. Classify the current price into a zone.
    5. Return scoring bonuses appropriate for ICT confluence.
    """
    highs = np.asarray(highs, dtype=float)
    lows = np.asarray(lows, dtype=float)
    closes = np.asarray(closes, dtype=float)

    n = len(closes)
    recent = min(lookback, n)

    h_slice = highs[n - recent:]
    l_slice = lows[n - recent:]
    c_slice = closes[n - recent:]
    slice_n = len(h_slice)

    current_price = float(c_slice[-1])

    # ── Attempt pivot-based swing detection ──
    pivot_window = 3
    sh = _find_swing_high(h_slice, window=pivot_window)
    sl = _find_swing_low(l_slice, window=pivot_window)

    # Sanity check — ensure sh > sl
    if sh <= sl:
        sh = float(np.max(h_slice))
        sl = float(np.min(l_slice))

    total_range = sh - sl

    # ── Flat market guard ──
    if total_range <= 0:
        flat_mid = (sh + sl) / 2.0
        return PremiumDiscountResult(
            swing_high=sh,
            swing_low=sl,
            equilibrium=flat_mid,
            current_pct=0.5,
            zone='equilibrium',
            is_discount=False,
            is_premium=False,
            discount_top=flat_mid,
            premium_bottom=flat_mid,
            fib_236=flat_mid,
            fib_382=flat_mid,
            fib_500=flat_mid,
            fib_618=flat_mid,
            fib_786=flat_mid,
            score_long=0,
            score_short=0,
        )

    # ── Fibonacci levels ──
    fib_236 = sl + 0.236 * total_range
    fib_382 = sl + 0.382 * total_range
    fib_500 = sl + 0.500 * total_range   # equilibrium
    fib_618 = sl + 0.618 * total_range
    fib_786 = sl + 0.786 * total_range

    current_pct = (current_price - sl) / total_range
    current_pct = max(0.0, min(1.0, current_pct))   # clamp to [0, 1]

    # ── Zone classification ──
    if current_pct <= 0.236:
        zone = 'deep_discount'
    elif current_pct <= 0.45:
        zone = 'discount'
    elif current_pct <= 0.55:
        zone = 'equilibrium'
    elif current_pct <= 0.786:
        zone = 'premium'
    else:
        zone = 'deep_premium'

    is_discount = current_pct < 0.5
    is_premium = current_pct > 0.5

    # ── Scoring ──
    # Deep zones get maximum confluence bonus; shallow zones get moderate bonus
    if zone == 'deep_discount':
        score_long = 15
        score_short = 0
    elif zone == 'discount':
        score_long = 10
        score_short = 0
    elif zone == 'equilibrium':
        score_long = 0
        score_short = 0
    elif zone == 'premium':
        score_long = 0
        score_short = 10
    else:   # deep_premium
        score_long = 0
        score_short = 15

    return PremiumDiscountResult(
        swing_high=round(sh, 8),
        swing_low=round(sl, 8),
        equilibrium=round(fib_500, 8),
        current_pct=round(current_pct, 4),
        zone=zone,
        is_discount=is_discount,
        is_premium=is_premium,
        discount_top=round(fib_382, 8),
        premium_bottom=round(fib_618, 8),
        fib_236=round(fib_236, 8),
        fib_382=round(fib_382, 8),
        fib_500=round(fib_500, 8),
        fib_618=round(fib_618, 8),
        fib_786=round(fib_786, 8),
        score_long=score_long,
        score_short=score_short,
    )
