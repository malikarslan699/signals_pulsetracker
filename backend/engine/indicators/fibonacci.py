"""
Fibonacci Tools — PulseSignal Pro
Implements: Fibonacci Retracement, OTE Zone detection, Fibonacci Extension TP targets.
"""
import numpy as np
from typing import Optional


# ─── Constants ────────────────────────────────────────────────────────────────

FIBO_RETRACEMENT_LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
FIBO_EXTENSION_LEVELS   = [1.272, 1.414, 1.618, 2.0, 2.618]


# ─── Fibonacci Retracement ────────────────────────────────────────────────────

def fibonacci_retracement(swing_low: float, swing_high: float,
                           direction: str = 'up') -> dict:
    """
    Calculate Fibonacci retracement and extension levels from a swing.

    For an upward move (direction='up'):
      Retracement level = swing_high - ratio * (swing_high - swing_low)
      (i.e. 0.0 = top of move, 1.0 = bottom of move)

    For a downward move (direction='down'):
      Retracement level = swing_low + ratio * (swing_high - swing_low)
      (i.e. 0.0 = bottom of move, 1.0 = top of move)

    Extension levels measure where price may travel beyond the swing.

    Returns
    -------
    dict with:
      'retracement' : {ratio: price, ...}
      'extensions'  : {ratio: price, ...}
      'swing_low'   : float
      'swing_high'  : float
      'range'       : float
    """
    swing_low  = float(swing_low)
    swing_high = float(swing_high)
    rng = swing_high - swing_low

    retracement: dict[float, float] = {}
    extensions:  dict[float, float] = {}

    direction = direction.lower()

    for ratio in FIBO_RETRACEMENT_LEVELS:
        if direction == 'up':
            retracement[ratio] = swing_high - ratio * rng
        else:  # down
            retracement[ratio] = swing_low + ratio * rng

    for ratio in FIBO_EXTENSION_LEVELS:
        if direction == 'up':
            extensions[ratio] = swing_high + (ratio - 1.0) * rng
        else:
            extensions[ratio] = swing_low - (ratio - 1.0) * rng

    return {
        'retracement': retracement,
        'extensions':  extensions,
        'swing_low':   swing_low,
        'swing_high':  swing_high,
        'range':       rng,
    }


# ─── Find Fibonacci Zone from Recent Price Action ────────────────────────────

def _find_swing_high_low(highs: np.ndarray, lows: np.ndarray,
                          lookback: int) -> tuple[float, float, int, int]:
    """
    Find the most significant swing high and low within the last `lookback` bars.
    Uses the absolute high and low with at least 5-bar separation.
    Returns (swing_high, swing_low, idx_high, idx_low).
    """
    n = len(highs)
    window_size = min(lookback, n)
    h_slice = highs[n - window_size:]
    l_slice = lows[n  - window_size:]

    idx_h = int(np.argmax(h_slice))
    idx_l = int(np.argmin(l_slice))
    sh = float(h_slice[idx_h])
    sl = float(l_slice[idx_l])

    # Global indices
    global_idx_h = (n - window_size) + idx_h
    global_idx_l = (n - window_size) + idx_l

    return sh, sl, global_idx_h, global_idx_l


def find_fib_retracement_zone(highs: np.ndarray, lows: np.ndarray,
                               closes: np.ndarray,
                               lookback: int = 50) -> dict:
    """
    1. Find the most recent significant swing high and low within `lookback` bars.
    2. Determine move direction (high before low = downward move, else upward).
    3. Calculate Fibonacci retracement and extension levels.
    4. Determine if current price is at a key Fibonacci level (±0.5%).

    OTE (Optimal Trade Entry) zone: between 0.618 and 0.786 retracement.
    Golden ratio: 0.618 level.
    """
    highs  = np.asarray(highs,  dtype=float)
    lows   = np.asarray(lows,   dtype=float)
    closes = np.asarray(closes, dtype=float)

    sh, sl, idx_h, idx_l = _find_swing_high_low(highs, lows, lookback)

    # Direction: if high came after low → price moved up (retrace down from high)
    # if low came after high → price moved down (retrace up from low)
    direction = 'up' if idx_l < idx_h else 'down'

    fib = fibonacci_retracement(sl, sh, direction)
    retracement = fib['retracement']
    extensions  = fib['extensions']
    rng = fib['range']

    close_now = float(closes[-1])
    tolerance = 0.005  # ±0.5%

    # Find which Fibonacci level price is closest to
    current_level: Optional[float] = None
    current_ratio: Optional[float] = None
    min_dist = float('inf')

    for ratio, price in retracement.items():
        dist = abs(close_now - price) / price if price != 0 else abs(close_now - price)
        if dist < min_dist:
            min_dist = dist
            current_level = price
            current_ratio = ratio

    # Only report if within tolerance
    if min_dist > tolerance:
        current_level = None
        current_ratio = None

    # Golden ratio check (0.618 ± 0.5%)
    golden_price = retracement.get(0.618, np.nan)
    at_golden_ratio = bool(
        not np.isnan(golden_price) and
        abs(close_now - golden_price) / golden_price <= tolerance
    )

    # OTE zone (0.618–0.786)
    ote_low_price  = retracement.get(0.618, np.nan)
    ote_high_price = retracement.get(0.786, np.nan)

    # For upward moves, 0.618 retrace is below 0.786 retrace
    # Ensure ote_low < ote_high
    if not np.isnan(ote_low_price) and not np.isnan(ote_high_price):
        ote_low_v  = min(ote_low_price, ote_high_price)
        ote_high_v = max(ote_low_price, ote_high_price)
    else:
        ote_low_v  = ote_low_price
        ote_high_v = ote_high_price

    at_ote_zone = bool(
        not np.isnan(ote_low_v) and not np.isnan(ote_high_v) and
        ote_low_v <= close_now <= ote_high_v
    )

    # Scoring
    score_long = 0
    score_short = 0
    if direction == 'up':
        # Bullish retracement setup
        if at_ote_zone:     score_long += 8
        if at_golden_ratio: score_long += 5
        if current_ratio in [0.5, 0.382]: score_long += 4
    else:
        # Bearish retracement setup
        if at_ote_zone:     score_short += 8
        if at_golden_ratio: score_short += 5
        if current_ratio in [0.5, 0.382]: score_short += 4

    return {
        'swing_high':       sh,
        'swing_low':        sl,
        'direction':        direction,
        'levels':           retracement,
        'extension_levels': extensions,
        'current_level':    current_level,
        'current_ratio':    current_ratio,
        'at_golden_ratio':  at_golden_ratio,
        'at_ote_zone':      at_ote_zone,
        'ote_low':          ote_low_v,
        'ote_high':         ote_high_v,
        'score_long':       score_long,
        'score_short':      score_short,
    }


# ─── Fibonacci Extension TP Targets ──────────────────────────────────────────

def calculate_tp_targets_fib(entry: float, stop_loss: float,
                              direction: str) -> dict:
    """
    Use Fibonacci extensions for TP levels based on risk range.
    risk = |entry - stop_loss|

    LONG:
      TP1 = entry + 1.272 * risk
      TP2 = entry + 1.618 * risk
      TP3 = entry + 2.618 * risk

    SHORT:
      TP1 = entry - 1.272 * risk
      TP2 = entry - 1.618 * risk
      TP3 = entry - 2.618 * risk

    RR ratios: distance to TP / risk
    """
    entry     = float(entry)
    stop_loss = float(stop_loss)
    risk      = abs(entry - stop_loss)

    if risk == 0:
        return {
            'tp1': entry, 'tp2': entry, 'tp3': entry,
            'rr1': 0.0,   'rr2': 0.0,  'rr3': 0.0,
        }

    direction = direction.upper()
    sign = 1.0 if direction == 'LONG' else -1.0

    tp1 = entry + sign * 1.272 * risk
    tp2 = entry + sign * 1.618 * risk
    tp3 = entry + sign * 2.618 * risk

    rr1 = abs(tp1 - entry) / risk  # = 1.272
    rr2 = abs(tp2 - entry) / risk  # = 1.618
    rr3 = abs(tp3 - entry) / risk  # = 2.618

    return {
        'tp1': round(tp1, 8),
        'tp2': round(tp2, 8),
        'tp3': round(tp3, 8),
        'rr1': round(rr1, 4),
        'rr2': round(rr2, 4),
        'rr3': round(rr3, 4),
    }
