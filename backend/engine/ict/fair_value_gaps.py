"""
ICT Fair Value Gaps (FVG) — PulseSignal Pro

FVG = 3-candle pattern where there is a price gap:
- Bullish FVG: candle[i-1].high < candle[i+1].low  (gap above candle i-1)
- Bearish FVG: candle[i-1].low > candle[i+1].high  (gap below candle i-1)

The FVG represents market inefficiency — price tends to return to fill it.
The middle candle (i) is the impulsive candle that created the gap.
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class FairValueGap:
    type: str             # 'bullish' or 'bearish'
    top: float            # top of the gap
    bottom: float         # bottom of the gap
    midpoint: float       # (top + bottom) / 2
    index: int            # index of the middle (impulse) candle
    timestamp: int
    is_filled: bool = False          # gap fully filled
    is_partially_filled: bool = False
    fill_pct: float = 0.0            # how much has been filled (0.0-1.0)
    strength: float = 0.0            # gap size / ATR at formation


def _compute_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                 period: int = 14) -> np.ndarray:
    """Compute Average True Range over the array."""
    n = len(closes)
    tr = np.zeros(n)
    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)
    tr[0] = highs[0] - lows[0]

    atr = np.zeros(n)
    atr[period - 1] = np.mean(tr[:period])
    for i in range(period, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    # Back-fill early values
    for i in range(period - 1):
        atr[i] = atr[period - 1]
    return atr


def detect_fvg(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    timestamps: np.ndarray,
    lookback: int = 100,
    min_gap_size_pct: float = 0.001,   # minimum 0.1% gap
) -> dict:
    """
    Detect all Fair Value Gaps and track their fill status.

    A Bullish FVG at index i (middle candle):
        gap_bottom = highs[i-1]
        gap_top    = lows[i+1]
        valid when gap_top > gap_bottom  (a real gap exists)

    A Bearish FVG at index i (middle candle):
        gap_top    = lows[i-1]
        gap_bottom = highs[i+1]
        valid when gap_top > gap_bottom  (a real gap exists)

    Fill tracking (for candles after the FVG):
        Bullish FVG: fills when price trades back down into [bottom, top].
            Partial fill: any candle's low < gap_top but high > gap_bottom.
            Full fill:    any candle's low <= gap_bottom.
        Bearish FVG: fills when price trades back up into [bottom, top].
            Partial fill: any candle's high > gap_bottom but low < gap_top.
            Full fill:    any candle's high >= gap_top.

    Returns:
    {
        'bullish_fvgs': list[FairValueGap],     # all detected (incl. filled)
        'bearish_fvgs': list[FairValueGap],
        'unfilled_bullish': list[FairValueGap],
        'unfilled_bearish': list[FairValueGap],
        'price_in_bullish_fvg': bool,
        'price_in_bearish_fvg': bool,
        'nearest_bullish_fvg': FairValueGap | None,
        'nearest_bearish_fvg': FairValueGap | None,
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

    atr = _compute_atr(highs, lows, closes, period=14)

    start = max(1, n - lookback)   # need i-1 and i+1, so start at 1
    end = n - 1                    # need i+1

    bullish_fvgs: list[FairValueGap] = []
    bearish_fvgs: list[FairValueGap] = []

    for i in range(start, end):
        # ── Bullish FVG ──
        gap_bottom = float(highs[i - 1])
        gap_top = float(lows[i + 1])

        if gap_top > gap_bottom:
            gap_size = gap_top - gap_bottom
            gap_size_pct = gap_size / gap_bottom if gap_bottom > 0 else 0.0

            if gap_size_pct >= min_gap_size_pct:
                atr_val = float(atr[i]) if atr[i] > 0 else gap_size
                strength = round(gap_size / atr_val, 3)

                fvg = FairValueGap(
                    type='bullish',
                    top=gap_top,
                    bottom=gap_bottom,
                    midpoint=round((gap_top + gap_bottom) / 2, 8),
                    index=i,
                    timestamp=int(timestamps[i]),
                    strength=strength,
                )

                # Fill tracking for all subsequent candles
                for k in range(i + 1, n):
                    candle_low = float(lows[k])
                    candle_high = float(highs[k])

                    if candle_low <= fvg.bottom:
                        # Fully filled — price traded through the entire gap
                        fvg.is_filled = True
                        fvg.is_partially_filled = True
                        fvg.fill_pct = 1.0
                        break
                    elif candle_low < fvg.top:
                        # Partially filled — price entered the gap from above
                        filled_amount = fvg.top - candle_low
                        fill_ratio = filled_amount / (fvg.top - fvg.bottom)
                        if fill_ratio > fvg.fill_pct:
                            fvg.fill_pct = round(min(fill_ratio, 1.0), 4)
                            fvg.is_partially_filled = True

                bullish_fvgs.append(fvg)

        # ── Bearish FVG ──
        gap_top_b = float(lows[i - 1])
        gap_bottom_b = float(highs[i + 1])

        if gap_top_b > gap_bottom_b:
            gap_size = gap_top_b - gap_bottom_b
            gap_size_pct = gap_size / gap_bottom_b if gap_bottom_b > 0 else 0.0

            if gap_size_pct >= min_gap_size_pct:
                atr_val = float(atr[i]) if atr[i] > 0 else gap_size
                strength = round(gap_size / atr_val, 3)

                fvg = FairValueGap(
                    type='bearish',
                    top=gap_top_b,
                    bottom=gap_bottom_b,
                    midpoint=round((gap_top_b + gap_bottom_b) / 2, 8),
                    index=i,
                    timestamp=int(timestamps[i]),
                    strength=strength,
                )

                # Fill tracking
                for k in range(i + 1, n):
                    candle_high = float(highs[k])
                    candle_low = float(lows[k])

                    if candle_high >= fvg.top:
                        # Fully filled
                        fvg.is_filled = True
                        fvg.is_partially_filled = True
                        fvg.fill_pct = 1.0
                        break
                    elif candle_high > fvg.bottom:
                        # Partially filled
                        filled_amount = candle_high - fvg.bottom
                        fill_ratio = filled_amount / (fvg.top - fvg.bottom)
                        if fill_ratio > fvg.fill_pct:
                            fvg.fill_pct = round(min(fill_ratio, 1.0), 4)
                            fvg.is_partially_filled = True

                bearish_fvgs.append(fvg)

    # ── Separate unfilled from filled ──
    unfilled_bullish = [f for f in bullish_fvgs if not f.is_filled]
    unfilled_bearish = [f for f in bearish_fvgs if not f.is_filled]

    # Sort by recency (most recent first)
    unfilled_bullish.sort(key=lambda x: x.index, reverse=True)
    unfilled_bearish.sort(key=lambda x: x.index, reverse=True)

    # ── Price-inside checks ──
    price_in_bull_fvg = any(f.bottom <= current_price <= f.top for f in unfilled_bullish)
    price_in_bear_fvg = any(f.bottom <= current_price <= f.top for f in unfilled_bearish)

    # ── Nearest unfilled FVG below current price (bullish magnet) ──
    nearest_bull_fvg: Optional[FairValueGap] = None
    candidates = [f for f in unfilled_bullish if f.top < current_price]
    if candidates:
        nearest_bull_fvg = max(candidates, key=lambda x: x.top)

    # ── Nearest unfilled FVG above current price (bearish magnet) ──
    nearest_bear_fvg: Optional[FairValueGap] = None
    candidates = [f for f in unfilled_bearish if f.bottom > current_price]
    if candidates:
        nearest_bear_fvg = min(candidates, key=lambda x: x.bottom)

    # ── Scoring ──
    score_long = 0
    score_short = 0

    if price_in_bull_fvg:
        # Check if it's a fresh (unfilled, never partially touched) FVG
        fresh = next(
            (f for f in unfilled_bullish
             if f.bottom <= current_price <= f.top and f.fill_pct == 0.0),
            None,
        )
        score_long = 20 if fresh else 12
    elif nearest_bull_fvg is not None:
        dist_pct = (current_price - nearest_bull_fvg.top) / current_price
        if dist_pct < 0.003:
            score_long = 8   # approaching bullish FVG from above

    if price_in_bear_fvg:
        fresh = next(
            (f for f in unfilled_bearish
             if f.bottom <= current_price <= f.top and f.fill_pct == 0.0),
            None,
        )
        score_short = 20 if fresh else 12
    elif nearest_bear_fvg is not None:
        dist_pct = (nearest_bear_fvg.bottom - current_price) / current_price
        if dist_pct < 0.003:
            score_short = 8   # approaching bearish FVG from below

    return {
        'bullish_fvgs': sorted(bullish_fvgs, key=lambda x: x.index, reverse=True),
        'bearish_fvgs': sorted(bearish_fvgs, key=lambda x: x.index, reverse=True),
        'unfilled_bullish': unfilled_bullish,
        'unfilled_bearish': unfilled_bearish,
        'price_in_bullish_fvg': price_in_bull_fvg,
        'price_in_bearish_fvg': price_in_bear_fvg,
        'nearest_bullish_fvg': nearest_bull_fvg,
        'nearest_bearish_fvg': nearest_bear_fvg,
        'score_long': score_long,
        'score_short': score_short,
        'total_bullish': len(bullish_fvgs),
        'total_bearish': len(bearish_fvgs),
        'total_unfilled_bullish': len(unfilled_bullish),
        'total_unfilled_bearish': len(unfilled_bearish),
    }
