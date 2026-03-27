"""
ICT Optimal Trade Entry (OTE) — PulseSignal Pro

OTE = The golden zone (0.618 to 0.786 Fibonacci retracement)
after a confirmed Break of Structure (BOS).

Setup logic:
1. Detect a significant impulse move (BOS) — a strong directional swing
2. Price retraces back into the 0.618-0.786 Fibonacci zone of that impulse
3. Entry is taken at 0.705 (midpoint of OTE zone)
4. Stop loss is placed just beyond the impulse origin (swing low/high)

Quality grades:
- A+: OTE zone aligns with an Order Block or FVG
- A:  Clean OTE with strong BOS
- B:  OTE with weak or ambiguous BOS
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class OTESetup:
    direction: str          # 'bullish' or 'bearish'
    impulse_start: float    # where impulse began (swing low for bull, swing high for bear)
    impulse_end: float      # where impulse ended (BOS level)
    ote_low: float          # 0.786 retracement (deeper end of zone)
    ote_high: float         # 0.618 retracement (shallow end of zone)
    entry: float            # 0.705 midpoint of OTE zone
    stop_loss: float        # beyond the impulse origin
    is_active: bool         # price currently inside the OTE zone
    quality: str            # 'A+', 'A', 'B'
    confidence: int         # 0-100
    index_start: int        # candle index of impulse origin
    index_end: int          # candle index of BOS


def _find_pivot_highs(highs: np.ndarray, window: int = 3) -> list[int]:
    n = len(highs)
    pivots = []
    for i in range(window, n - window):
        if all(highs[i] > highs[i - k] for k in range(1, window + 1)) and \
           all(highs[i] > highs[i + k] for k in range(1, window + 1)):
            pivots.append(i)
    return pivots


def _find_pivot_lows(lows: np.ndarray, window: int = 3) -> list[int]:
    n = len(lows)
    pivots = []
    for i in range(window, n - window):
        if all(lows[i] < lows[i - k] for k in range(1, window + 1)) and \
           all(lows[i] < lows[i + k] for k in range(1, window + 1)):
            pivots.append(i)
    return pivots


def _score_quality(impulse_size: float, candle_range_avg: float,
                   bos_confirmed: bool) -> tuple[str, int]:
    """Grade the OTE setup quality."""
    ratio = impulse_size / candle_range_avg if candle_range_avg > 0 else 0
    if bos_confirmed and ratio >= 5:
        return 'A+', 90
    elif bos_confirmed and ratio >= 3:
        return 'A', 75
    else:
        return 'B', 55


def detect_ote(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    timestamps: np.ndarray,
    lookback: int = 50,
) -> dict:
    """
    Detect Optimal Trade Entry (OTE) setups by:

    1. Scanning for significant impulse moves within the lookback window.
       A bullish impulse: swing low -> swing high where the move is
       >= 3x the average candle range. This constitutes a BOS.

    2. Computing Fibonacci retracement levels:
         Bullish OTE zone: [impulse * 0.786 back from top,
                            impulse * 0.618 back from top]
         Bearish OTE zone: [impulse * 0.618 up from bottom,
                            impulse * 0.786 up from bottom]

    3. Checking if current price sits inside the OTE zone.

    4. Grading setup quality based on impulse strength.

    Returns:
    {
        'setups': list[OTESetup],
        'active_setup': OTESetup | None,
        'price_in_ote': bool,
        'ote_low': float | None,
        'ote_high': float | None,
        'score_long': int,
        'score_short': int,
    }
    """
    highs = np.asarray(highs, dtype=float)
    lows = np.asarray(lows, dtype=float)
    closes = np.asarray(closes, dtype=float)
    timestamps = np.asarray(timestamps)

    n = len(closes)
    current_price = float(closes[-1])
    start = max(0, n - lookback)

    h_slice = highs[start:]
    l_slice = lows[start:]
    c_slice = closes[start:]
    slice_n = len(h_slice)

    # Average candle range over lookback for quality grading
    avg_range = float(np.mean(h_slice - l_slice)) if slice_n > 0 else 1.0

    pivot_window = 3
    ph_indices = _find_pivot_highs(h_slice, window=pivot_window)
    pl_indices = _find_pivot_lows(l_slice, window=pivot_window)

    setups: list[OTESetup] = []

    # ── Bullish OTE: swing low -> swing high impulse, then retrace into 0.618-0.786 ──
    for sl_idx in pl_indices:
        sl_price = float(l_slice[sl_idx])
        # Find the next swing high after this swing low
        subsequent_sh = [i for i in ph_indices if i > sl_idx]
        if not subsequent_sh:
            continue
        sh_idx = subsequent_sh[0]
        sh_price = float(h_slice[sh_idx])

        impulse = sh_price - sl_price
        if impulse <= 0 or impulse < 3 * avg_range:
            continue   # Too small — not a valid BOS

        # Fibonacci retracement levels (from swing high, measuring down)
        fib_618 = sh_price - 0.618 * impulse   # 0.618 retrace level
        fib_786 = sh_price - 0.786 * impulse   # 0.786 retrace level
        entry = sh_price - 0.705 * impulse      # 0.705 midpoint

        ote_high = fib_618   # top of OTE zone (less deep)
        ote_low = fib_786    # bottom of OTE zone (deeper)
        stop_loss = sl_price - (impulse * 0.1)   # 10% below swing low

        # Check if price has retraced into the OTE zone
        # Look at candles after the swing high
        retraced = False
        for k in range(sh_idx + 1, slice_n):
            if l_slice[k] <= ote_high:
                retraced = True
                break

        is_active = ote_low <= current_price <= ote_high

        # BOS confirmed if impulse broke a prior swing high
        prior_sh = [i for i in ph_indices if i < sl_idx]
        bos_confirmed = True
        if prior_sh:
            prior_peak = float(h_slice[prior_sh[-1]])
            bos_confirmed = sh_price > prior_peak

        quality, confidence = _score_quality(impulse, avg_range, bos_confirmed)

        setup = OTESetup(
            direction='bullish',
            impulse_start=round(sl_price, 8),
            impulse_end=round(sh_price, 8),
            ote_low=round(ote_low, 8),
            ote_high=round(ote_high, 8),
            entry=round(entry, 8),
            stop_loss=round(stop_loss, 8),
            is_active=is_active,
            quality=quality,
            confidence=confidence,
            index_start=start + sl_idx,
            index_end=start + sh_idx,
        )
        setups.append(setup)

    # ── Bearish OTE: swing high -> swing low impulse, then retrace up into 0.618-0.786 ──
    for sh_idx in ph_indices:
        sh_price = float(h_slice[sh_idx])
        subsequent_sl = [i for i in pl_indices if i > sh_idx]
        if not subsequent_sl:
            continue
        sl_idx = subsequent_sl[0]
        sl_price = float(l_slice[sl_idx])

        impulse = sh_price - sl_price
        if impulse <= 0 or impulse < 3 * avg_range:
            continue

        # Fibonacci retracement (from swing low, measuring up)
        fib_618 = sl_price + 0.618 * impulse
        fib_786 = sl_price + 0.786 * impulse
        entry = sl_price + 0.705 * impulse

        ote_low = fib_618    # bottom of OTE zone (less deep retrace)
        ote_high = fib_786   # top of OTE zone (deeper retrace)
        stop_loss = sh_price + (impulse * 0.1)

        # Check if price has retraced up into the OTE zone
        retraced = False
        for k in range(sl_idx + 1, slice_n):
            if h_slice[k] >= ote_low:
                retraced = True
                break

        is_active = ote_low <= current_price <= ote_high

        prior_sl = [i for i in pl_indices if i < sh_idx]
        bos_confirmed = True
        if prior_sl:
            prior_trough = float(l_slice[prior_sl[-1]])
            bos_confirmed = sl_price < prior_trough

        quality, confidence = _score_quality(impulse, avg_range, bos_confirmed)

        setup = OTESetup(
            direction='bearish',
            impulse_start=round(sh_price, 8),
            impulse_end=round(sl_price, 8),
            ote_low=round(ote_low, 8),
            ote_high=round(ote_high, 8),
            entry=round(entry, 8),
            stop_loss=round(stop_loss, 8),
            is_active=is_active,
            quality=quality,
            confidence=confidence,
            index_start=start + sh_idx,
            index_end=start + sl_idx,
        )
        setups.append(setup)

    # ── Active setups ──
    active_setups = [s for s in setups if s.is_active]

    # Pick the highest-quality active setup
    active_setup: Optional[OTESetup] = None
    if active_setups:
        grade_order = {'A+': 0, 'A': 1, 'B': 2}
        active_setup = min(active_setups, key=lambda s: (grade_order.get(s.quality, 3), -s.confidence))

    price_in_ote = active_setup is not None

    ote_low_val: Optional[float] = active_setup.ote_low if active_setup else None
    ote_high_val: Optional[float] = active_setup.ote_high if active_setup else None

    # ── Scoring ──
    score_long = 0
    score_short = 0

    if active_setup:
        quality_scores = {'A+': 25, 'A': 20, 'B': 12}
        q_score = quality_scores.get(active_setup.quality, 10)
        if active_setup.direction == 'bullish':
            score_long = q_score
        else:
            score_short = q_score
    else:
        # Check if price is approaching any OTE zone (within 0.3%)
        for s in setups[-10:]:   # check last 10 setups
            approach_dist = abs(current_price - s.entry) / current_price
            if approach_dist < 0.003:
                if s.direction == 'bullish':
                    score_long = max(score_long, 8)
                else:
                    score_short = max(score_short, 8)

    return {
        'setups': sorted(setups, key=lambda x: x.index_start, reverse=True),
        'active_setup': active_setup,
        'price_in_ote': price_in_ote,
        'ote_low': ote_low_val,
        'ote_high': ote_high_val,
        'score_long': score_long,
        'score_short': score_short,
        'total_setups': len(setups),
        'active_count': len(active_setups),
    }
