"""
ICT Daily Bias Analysis — PulseSignal Pro

Daily bias = HTF (Higher Timeframe) analysis to determine the most likely
direction for the current trading session.

Analysis factors:
1. Where is price relative to the previous day's range (PDH/PDL)?
2. Has price swept daily liquidity (stop hunt above PDH or below PDL)?
3. Is price in premium or discount on the current timeframe?
4. What is the weekly trend direction (last 5 daily candles)?
5. Institutional order flow via consecutive closes above/below PDH/PDL.
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class DailyBiasResult:
    bias: str               # 'bullish', 'bearish', or 'neutral'
    confidence: int         # 0-100
    reasons: list[str]      # human-readable reasons driving the bias
    score_long: int
    score_short: int
    pdh: Optional[float]    # previous day high
    pdl: Optional[float]    # previous day low
    above_pdh: bool         # current price > PDH
    below_pdl: bool         # current price < PDL
    swept_pdh: bool         # price briefly exceeded PDH then reversed (bear setup)
    swept_pdl: bool         # price briefly went below PDL then reversed (bull setup)
    weekly_trend: str       # 'bullish', 'bearish', or 'neutral'
    price_vs_pdh_pct: float # (price - pdh) / pdh  — positive = above
    price_vs_pdl_pct: float # (price - pdl) / pdl  — negative = below


# Approximate candles per day for common timeframes
CANDLES_PER_DAY: dict[str, int] = {
    '1m':  1440,
    '3m':  480,
    '5m':  288,
    '15m': 96,
    '30m': 48,
    '1H':  24,
    '2H':  12,
    '4H':  6,
    '8H':  3,
    '1D':  1,
    '1W':  1,
}


def _weekly_trend(closes: np.ndarray, cpd: int) -> str:
    """
    Determine the weekly trend by comparing the open of 5 days ago
    to the most recent close.  Returns 'bullish', 'bearish', or 'neutral'.
    """
    weekly_bars = 5 * cpd
    n = len(closes)
    if n < weekly_bars + 1:
        weekly_bars = n - 1
    if weekly_bars <= 0:
        return 'neutral'

    start_price = float(closes[n - weekly_bars - 1])
    end_price = float(closes[-1])

    diff_pct = (end_price - start_price) / start_price if start_price > 0 else 0.0

    if diff_pct > 0.002:    # +0.2% threshold to call it bullish
        return 'bullish'
    elif diff_pct < -0.002:
        return 'bearish'
    return 'neutral'


def _consecutive_closes(closes: np.ndarray, level: float, above: bool,
                        min_count: int = 3) -> bool:
    """
    Check if the last `min_count` closes are all above (or below) `level`.
    Used to confirm institutional commitment to a direction.
    """
    n = len(closes)
    if n < min_count:
        return False
    recent = closes[-min_count:]
    if above:
        return all(float(c) > level for c in recent)
    return all(float(c) < level for c in recent)


def analyze_daily_bias(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    timestamps: np.ndarray,
    current_timeframe: str = '1H',
) -> DailyBiasResult:
    """
    Analyze price action relative to the previous day's range to establish
    the current session's directional bias.

    Steps:
    1. Determine the number of candles per day for the given timeframe.
    2. Slice out the previous day's OHLC data to compute PDH and PDL.
    3. Determine current price position vs PDH/PDL.
    4. Detect liquidity sweeps: a candle whose wick breaches PDH/PDL
       but whose close is on the other side of the level.
    5. Compute weekly trend from 5 days of prior closes.
    6. Weight signals and produce a directional bias with confidence.

    Returns a DailyBiasResult with full analysis and score contributions.
    """
    highs = np.asarray(highs, dtype=float)
    lows = np.asarray(lows, dtype=float)
    closes = np.asarray(closes, dtype=float)
    timestamps = np.asarray(timestamps)

    n = len(closes)

    # Minimum data guard
    if n < 10:
        return DailyBiasResult(
            bias='neutral', confidence=0, reasons=['Insufficient data'],
            score_long=0, score_short=0,
            pdh=None, pdl=None,
            above_pdh=False, below_pdl=False,
            swept_pdh=False, swept_pdl=False,
            weekly_trend='neutral',
            price_vs_pdh_pct=0.0, price_vs_pdl_pct=0.0,
        )

    current_price = float(closes[-1])
    reasons: list[str] = []
    score_long = 0
    score_short = 0

    cpd = CANDLES_PER_DAY.get(current_timeframe, 24)

    # ── Previous day OHLC ──
    # "Previous day" = the block of cpd candles ending cpd bars before now
    prev_end = max(1, n - cpd)
    prev_start = max(0, prev_end - cpd)

    if prev_start < prev_end:
        pdh: Optional[float] = float(np.max(highs[prev_start:prev_end]))
        pdl: Optional[float] = float(np.min(lows[prev_start:prev_end]))
    else:
        # Not enough data for a full previous day — use first half of available
        mid = n // 2
        pdh = float(np.max(highs[:mid])) if mid > 0 else None
        pdl = float(np.min(lows[:mid])) if mid > 0 else None

    # ── Position vs PDH/PDL ──
    above_pdh = pdh is not None and current_price > pdh
    below_pdl = pdl is not None and current_price < pdl

    price_vs_pdh_pct = ((current_price - pdh) / pdh) if pdh else 0.0
    price_vs_pdl_pct = ((current_price - pdl) / pdl) if pdl else 0.0

    # ── Liquidity sweep detection (last 5 candles + current day) ──
    look = min(5, n)
    recent_highs = highs[-look:]
    recent_lows = lows[-look:]
    recent_closes = closes[-look:]

    swept_pdh = False
    swept_pdl = False

    if pdh is not None:
        for k in range(look):
            # Wick above PDH but closed below PDH = sweep of BSL -> bear setup
            if float(recent_highs[k]) > pdh and float(recent_closes[k]) < pdh:
                swept_pdh = True
                break

    if pdl is not None:
        for k in range(look):
            # Wick below PDL but closed above PDL = sweep of SSL -> bull setup
            if float(recent_lows[k]) < pdl and float(recent_closes[k]) > pdl:
                swept_pdl = True
                break

    # ── Weekly trend ──
    weekly = _weekly_trend(closes, cpd)

    # ── Institutional order flow: consecutive closes ──
    inst_long = pdh is not None and _consecutive_closes(closes, pdh, above=True, min_count=3)
    inst_short = pdl is not None and _consecutive_closes(closes, pdl, above=False, min_count=3)

    # ── Signal weighting ──
    bull_weight = 0
    bear_weight = 0

    # Liquidity sweeps are the strongest signal (+3 weight, +15 score)
    if swept_pdl:
        bull_weight += 3
        score_long += 15
        reasons.append(f"PDL swept ({pdl:.5g}) — stop hunt below, bullish reversal expected")

    if swept_pdh:
        bear_weight += 3
        score_short += 15
        reasons.append(f"PDH swept ({pdh:.5g}) — stop hunt above, bearish reversal expected")

    # Price above PDH without sweep = bullish momentum (+2, +8)
    if above_pdh and not swept_pdh:
        bull_weight += 2
        score_long += 8
        reasons.append(f"Price above PDH ({pdh:.5g}) — bullish breakout momentum")

    # Price below PDL without sweep = bearish momentum (+2, +8)
    if below_pdl and not swept_pdl:
        bear_weight += 2
        score_short += 8
        reasons.append(f"Price below PDL ({pdl:.5g}) — bearish breakdown momentum")

    # Institutional consecutive closes (+2, +10)
    if inst_long:
        bull_weight += 2
        score_long += 10
        reasons.append("3+ consecutive closes above PDH — institutional buy pressure")

    if inst_short:
        bear_weight += 2
        score_short += 10
        reasons.append("3+ consecutive closes below PDL — institutional sell pressure")

    # Weekly trend (+1, +5)
    if weekly == 'bullish':
        bull_weight += 1
        score_long += 5
        reasons.append("Weekly trend bullish (HTF alignment)")
    elif weekly == 'bearish':
        bear_weight += 1
        score_short += 5
        reasons.append("Weekly trend bearish (HTF alignment)")
    else:
        reasons.append("Weekly trend neutral")

    # Price in mid-range and no sweep = neutral hints
    if pdh is not None and pdl is not None:
        mid_range = (pdh + pdl) / 2.0
        if not swept_pdh and not swept_pdl and not above_pdh and not below_pdl:
            if current_price > mid_range:
                bear_weight += 1
                score_short += 3
                reasons.append(f"Price in premium of prior range (above mid {mid_range:.5g})")
            else:
                bull_weight += 1
                score_long += 3
                reasons.append(f"Price in discount of prior range (below mid {mid_range:.5g})")

    # ── Determine bias ──
    total = bull_weight + bear_weight

    if bull_weight > bear_weight:
        bias = 'bullish'
        confidence = int((bull_weight / max(total, 1)) * 100)
        score_short = 0   # don't double-score opposing direction
    elif bear_weight > bull_weight:
        bias = 'bearish'
        confidence = int((bear_weight / max(total, 1)) * 100)
        score_long = 0
    else:
        bias = 'neutral'
        confidence = 0
        score_long = 0
        score_short = 0
        reasons.append("Balanced signals — no clear bias")

    return DailyBiasResult(
        bias=bias,
        confidence=confidence,
        reasons=reasons,
        score_long=score_long,
        score_short=score_short,
        pdh=pdh,
        pdl=pdl,
        above_pdh=above_pdh,
        below_pdl=below_pdl,
        swept_pdh=swept_pdh,
        swept_pdl=swept_pdl,
        weekly_trend=weekly,
        price_vs_pdh_pct=round(price_vs_pdh_pct, 6),
        price_vs_pdl_pct=round(price_vs_pdl_pct, 6),
    )
