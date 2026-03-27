"""
ICT Breaker Blocks — PulseSignal Pro

A Breaker Block forms when:
1. A valid Order Block exists (bullish or bearish).
2. Price mitigates (fully trades through) the Order Block — the OB fails
   to hold as support or resistance.
3. The failed OB now flips its role:
   - Failed Bullish OB  -> Bearish Breaker Block (now acts as resistance)
   - Failed Bearish OB  -> Bullish Breaker Block (now acts as support)

Price tends to revisit these breaker zones before continuing in the
direction of the break, making them high-probability re-entry areas.
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class BreakerBlock:
    type: str           # 'bullish_breaker' or 'bearish_breaker'
    high: float
    low: float
    index: int          # original OB candle index
    timestamp: int
    is_tested: bool = False      # has price revisited the breaker zone?
    times_tested: int = 0
    original_ob_type: str = ''   # 'bullish' or 'bearish' (the OB that failed)


def detect_breaker_blocks(
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    timestamps: np.ndarray,
    lookback: int = 100,
) -> dict:
    """
    Detect Breaker Blocks by:

    1. Running the full Order Block detection algorithm.
    2. Collecting all OBs that have been fully mitigated
       (price traded through the entire OB zone).
    3. Classifying those failed OBs as breaker blocks with inverted roles:
         - Mitigated bullish OB   -> bearish_breaker  (was support, now resistance)
         - Mitigated bearish OB   -> bullish_breaker  (was resistance, now support)
    4. Checking whether the current price is near (within 0.3%) a breaker zone.

    Returns:
    {
        'bullish_breakers': list[BreakerBlock],
        'bearish_breakers': list[BreakerBlock],
        'price_at_bullish_breaker': bool,
        'price_at_bearish_breaker': bool,
        'nearest_bullish_breaker': BreakerBlock | None,
        'nearest_bearish_breaker': BreakerBlock | None,
        'score_long': int,
        'score_short': int,
    }
    """
    from .order_blocks import detect_order_blocks

    opens = np.asarray(opens, dtype=float)
    highs = np.asarray(highs, dtype=float)
    lows = np.asarray(lows, dtype=float)
    closes = np.asarray(closes, dtype=float)
    timestamps = np.asarray(timestamps)

    n = len(closes)
    current_price = float(closes[-1])

    # ── Run OB detection with a synthetic volume array ──
    volumes = np.ones(n, dtype=float)
    ob_result = detect_order_blocks(
        opens, highs, lows, closes, volumes, timestamps,
        lookback=lookback,
        min_impulse_ratio=2.0,
        min_candles_in_impulse=2,
    )

    # ── We need the full OB sets including mitigated ones.
    #    Re-run a lightweight scan to collect mitigated OBs. ──
    start = max(0, n - lookback)
    min_impulse_ratio = 2.0
    min_candles_in_impulse = 2

    mitigated_bullish_obs: list[dict] = []
    mitigated_bearish_obs: list[dict] = []

    for i in range(start, n - min_candles_in_impulse - 1):
        candle_range = highs[i] - lows[i]
        if candle_range <= 0:
            continue

        is_bearish_candle = closes[i] < opens[i]
        is_bullish_candle = closes[i] > opens[i]

        # ── Check for bullish OB that later got mitigated ──
        if is_bearish_candle:
            impulse_high = highs[i + 1]
            impulse_candles = 0
            for j in range(i + 1, min(i + 6, n)):
                if closes[j] > opens[j]:
                    impulse_candles += 1
                    impulse_high = max(impulse_high, highs[j])
                else:
                    break
            if impulse_candles >= min_candles_in_impulse:
                total_impulse = impulse_high - lows[i]
                if total_impulse >= min_impulse_ratio * candle_range:
                    ob_high = float(highs[i])
                    ob_low = float(lows[i])
                    # Check if fully mitigated (price below ob_low)
                    mitigated = False
                    for k in range(i + impulse_candles + 1, n):
                        if lows[k] <= ob_low:
                            mitigated = True
                            break
                    if mitigated:
                        mitigated_bullish_obs.append({
                            'high': ob_high, 'low': ob_low,
                            'index': i, 'timestamp': int(timestamps[i]),
                        })

        # ── Check for bearish OB that later got mitigated ──
        if is_bullish_candle:
            impulse_low = lows[i + 1]
            impulse_candles = 0
            for j in range(i + 1, min(i + 6, n)):
                if closes[j] < opens[j]:
                    impulse_candles += 1
                    impulse_low = min(impulse_low, lows[j])
                else:
                    break
            if impulse_candles >= min_candles_in_impulse:
                total_impulse = highs[i] - impulse_low
                if total_impulse >= min_impulse_ratio * candle_range:
                    ob_high = float(highs[i])
                    ob_low = float(lows[i])
                    mitigated = False
                    for k in range(i + impulse_candles + 1, n):
                        if highs[k] >= ob_high:
                            mitigated = True
                            break
                    if mitigated:
                        mitigated_bearish_obs.append({
                            'high': ob_high, 'low': ob_low,
                            'index': i, 'timestamp': int(timestamps[i]),
                        })

    # ── Convert mitigated OBs to Breaker Blocks ──
    bullish_breakers: list[BreakerBlock] = []   # from failed bearish OBs
    bearish_breakers: list[BreakerBlock] = []   # from failed bullish OBs

    tolerance = 0.003   # 0.3% proximity tolerance

    for ob in mitigated_bullish_obs:
        bb = BreakerBlock(
            type='bearish_breaker',
            high=ob['high'],
            low=ob['low'],
            index=ob['index'],
            timestamp=ob['timestamp'],
            original_ob_type='bullish',
        )
        # Count how many times price has revisited the breaker zone after it formed
        for k in range(ob['index'] + 1, n):
            candle_touches_zone = (lows[k] <= bb.high * (1 + tolerance) and
                                   highs[k] >= bb.low * (1 - tolerance))
            if candle_touches_zone:
                bb.times_tested += 1
                bb.is_tested = True
        bearish_breakers.append(bb)

    for ob in mitigated_bearish_obs:
        bb = BreakerBlock(
            type='bullish_breaker',
            high=ob['high'],
            low=ob['low'],
            index=ob['index'],
            timestamp=ob['timestamp'],
            original_ob_type='bearish',
        )
        for k in range(ob['index'] + 1, n):
            candle_touches_zone = (lows[k] <= bb.high * (1 + tolerance) and
                                   highs[k] >= bb.low * (1 - tolerance))
            if candle_touches_zone:
                bb.times_tested += 1
                bb.is_tested = True
        bullish_breakers.append(bb)

    # ── Price proximity checks ──
    price_at_bull_breaker = any(
        bb.low * (1 - tolerance) <= current_price <= bb.high * (1 + tolerance)
        for bb in bullish_breakers
    )
    price_at_bear_breaker = any(
        bb.low * (1 - tolerance) <= current_price <= bb.high * (1 + tolerance)
        for bb in bearish_breakers
    )

    # ── Nearest breakers ──
    nearest_bull_breaker: Optional[BreakerBlock] = None
    below_bulls = [bb for bb in bullish_breakers if bb.high <= current_price]
    if below_bulls:
        nearest_bull_breaker = max(below_bulls, key=lambda x: x.high)

    nearest_bear_breaker: Optional[BreakerBlock] = None
    above_bears = [bb for bb in bearish_breakers if bb.low >= current_price]
    if above_bears:
        nearest_bear_breaker = min(above_bears, key=lambda x: x.low)

    # ── Scoring ──
    score_long = 0
    score_short = 0

    if price_at_bull_breaker:
        # Untested breakers are higher probability
        fresh = any(
            bb.low * (1 - tolerance) <= current_price <= bb.high * (1 + tolerance)
            and not bb.is_tested
            for bb in bullish_breakers
        )
        score_long = 18 if fresh else 12
    elif nearest_bull_breaker is not None:
        dist_pct = (current_price - nearest_bull_breaker.high) / current_price
        if 0 <= dist_pct < 0.005:
            score_long = 8

    if price_at_bear_breaker:
        fresh = any(
            bb.low * (1 - tolerance) <= current_price <= bb.high * (1 + tolerance)
            and not bb.is_tested
            for bb in bearish_breakers
        )
        score_short = 18 if fresh else 12
    elif nearest_bear_breaker is not None:
        dist_pct = (nearest_bear_breaker.low - current_price) / current_price
        if 0 <= dist_pct < 0.005:
            score_short = 8

    return {
        'bullish_breakers': sorted(bullish_breakers, key=lambda x: x.index, reverse=True),
        'bearish_breakers': sorted(bearish_breakers, key=lambda x: x.index, reverse=True),
        'price_at_bullish_breaker': price_at_bull_breaker,
        'price_at_bearish_breaker': price_at_bear_breaker,
        'nearest_bullish_breaker': nearest_bull_breaker,
        'nearest_bearish_breaker': nearest_bear_breaker,
        'score_long': score_long,
        'score_short': score_short,
        'total_bullish': len(bullish_breakers),
        'total_bearish': len(bearish_breakers),
    }
