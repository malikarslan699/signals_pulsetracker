"""
ICT Order Blocks Detection — PulseSignal Pro

An Order Block is:
- BULLISH OB: The last BEARISH candle before a strong bullish impulse
- BEARISH OB: The last BULLISH candle before a strong bearish impulse

The impulse must:
- Move at least 3x the OB candle's range
- Consist of 2+ consecutive candles in the same direction
- Leave the OB zone unmitigated (price hasn't returned to it)
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class OrderBlock:
    type: str           # 'bullish' or 'bearish'
    high: float         # top of OB zone
    low: float          # bottom of OB zone
    open: float         # OB candle open
    close: float        # OB candle close
    index: int          # candle index in array
    timestamp: int      # unix ms
    is_mitigated: bool = False   # has price returned and touched it
    is_breaker: bool = False     # has OB failed (become breaker block)
    strength: int = 0   # 1-5 strength score based on impulse size
    impulse_size: float = 0.0   # size of move that created this OB
    times_tested: int = 0


def detect_order_blocks(
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    volumes: np.ndarray,
    timestamps: np.ndarray,
    lookback: int = 100,
    min_impulse_ratio: float = 2.0,
    min_candles_in_impulse: int = 2,
) -> dict:
    """
    Detect all Order Blocks in the given candle data.

    Algorithm:
    1. For each candle, check if it starts an impulse move
       - Impulse = 2+ consecutive candles moving same direction
       - Impulse range >= min_impulse_ratio x OB candle range
    2. The last opposing-color candle before impulse = Order Block
    3. Check if OB is still active (not mitigated)
    4. Score OB by impulse strength

    Returns:
    {
        'bullish_obs': list[OrderBlock],   # sorted by recency
        'bearish_obs': list[OrderBlock],
        'nearest_bullish_ob': OrderBlock | None,  # closest below price
        'nearest_bearish_ob': OrderBlock | None,  # closest above price
        'price_in_bullish_ob': bool,  # current price inside a bullish OB
        'price_in_bearish_ob': bool,
        'score_long': int,   # +20 fresh OB, +15 tested OB
        'score_short': int,
        'active_obs': list[OrderBlock]  # all non-mitigated OBs
    }
    """
    opens = np.asarray(opens, dtype=float)
    highs = np.asarray(highs, dtype=float)
    lows = np.asarray(lows, dtype=float)
    closes = np.asarray(closes, dtype=float)
    timestamps = np.asarray(timestamps)

    bullish_obs = []
    bearish_obs = []

    current_price = float(closes[-1])
    n = len(closes)
    start = max(0, n - lookback)

    for i in range(start, n - min_candles_in_impulse - 1):
        candle_range = highs[i] - lows[i]
        if candle_range <= 0:
            continue

        is_bearish_candle = closes[i] < opens[i]
        is_bullish_candle = closes[i] > opens[i]

        # ── BULLISH Order Block: last bearish candle before bullish impulse ──
        if is_bearish_candle:
            impulse_high = highs[i + 1]
            impulse_candles = 0

            for j in range(i + 1, min(i + 1 + 5, n)):
                if closes[j] > opens[j]:   # bullish candle
                    impulse_candles += 1
                    impulse_high = max(impulse_high, highs[j])
                else:
                    break

            if impulse_candles >= min_candles_in_impulse:
                total_impulse = impulse_high - lows[i]
                if total_impulse >= min_impulse_ratio * candle_range:
                    strength = min(5, max(1, int(total_impulse / candle_range)))
                    ob = OrderBlock(
                        type='bullish',
                        high=float(highs[i]),
                        low=float(lows[i]),
                        open=float(opens[i]),
                        close=float(closes[i]),
                        index=i,
                        timestamp=int(timestamps[i]),
                        strength=strength,
                        impulse_size=float(total_impulse),
                    )

                    # Mitigation check: has price returned into this OB zone?
                    for k in range(i + impulse_candles + 1, n):
                        if lows[k] <= ob.high:
                            ob.times_tested += 1
                            if lows[k] <= ob.low:
                                ob.is_mitigated = True
                                break

                    bullish_obs.append(ob)

        # ── BEARISH Order Block: last bullish candle before bearish impulse ──
        if is_bullish_candle:
            impulse_low = lows[i + 1]
            impulse_candles = 0

            for j in range(i + 1, min(i + 1 + 5, n)):
                if closes[j] < opens[j]:   # bearish candle
                    impulse_candles += 1
                    impulse_low = min(impulse_low, lows[j])
                else:
                    break

            if impulse_candles >= min_candles_in_impulse:
                total_impulse = highs[i] - impulse_low
                if total_impulse >= min_impulse_ratio * candle_range:
                    strength = min(5, max(1, int(total_impulse / candle_range)))
                    ob = OrderBlock(
                        type='bearish',
                        high=float(highs[i]),
                        low=float(lows[i]),
                        open=float(opens[i]),
                        close=float(closes[i]),
                        index=i,
                        timestamp=int(timestamps[i]),
                        strength=strength,
                        impulse_size=float(total_impulse),
                    )

                    for k in range(i + impulse_candles + 1, n):
                        if highs[k] >= ob.low:
                            ob.times_tested += 1
                            if highs[k] >= ob.high:
                                ob.is_mitigated = True
                                break

                    bearish_obs.append(ob)

    # ── Active (unmitigated) OBs ──
    active_bullish = [ob for ob in bullish_obs if not ob.is_mitigated]
    active_bearish = [ob for ob in bearish_obs if not ob.is_mitigated]

    # ── Nearest OB below current price (bullish support) ──
    nearest_bull_ob: Optional[OrderBlock] = None
    candidates_bull = [ob for ob in active_bullish if ob.high <= current_price]
    if candidates_bull:
        nearest_bull_ob = max(candidates_bull, key=lambda x: x.high)

    # ── Nearest OB above current price (bearish resistance) ──
    nearest_bear_ob: Optional[OrderBlock] = None
    candidates_bear = [ob for ob in active_bearish if ob.low >= current_price]
    if candidates_bear:
        nearest_bear_ob = min(candidates_bear, key=lambda x: x.low)

    # ── Price-inside checks ──
    price_in_bull_ob = any(ob.low <= current_price <= ob.high for ob in active_bullish)
    price_in_bear_ob = any(ob.low <= current_price <= ob.high for ob in active_bearish)

    # ── Scoring ──
    score_long = 0
    score_short = 0

    if price_in_bull_ob:
        fresh_ob = next(
            (ob for ob in active_bullish
             if ob.low <= current_price <= ob.high and ob.times_tested == 0),
            None,
        )
        score_long = 25 if fresh_ob else 18
    elif nearest_bull_ob is not None:
        dist_pct = (current_price - nearest_bull_ob.high) / current_price
        if 0 <= dist_pct < 0.005:
            score_long = 15  # approaching bullish OB

    if price_in_bear_ob:
        fresh_ob = next(
            (ob for ob in active_bearish
             if ob.low <= current_price <= ob.high and ob.times_tested == 0),
            None,
        )
        score_short = 25 if fresh_ob else 18
    elif nearest_bear_ob is not None:
        dist_pct = (nearest_bear_ob.low - current_price) / current_price
        if 0 <= dist_pct < 0.005:
            score_short = 15

    all_active = sorted(
        active_bullish + active_bearish,
        key=lambda x: x.index,
        reverse=True,
    )

    return {
        'bullish_obs': sorted(active_bullish, key=lambda x: x.index, reverse=True),
        'bearish_obs': sorted(active_bearish, key=lambda x: x.index, reverse=True),
        'nearest_bullish_ob': nearest_bull_ob,
        'nearest_bearish_ob': nearest_bear_ob,
        'price_in_bullish_ob': price_in_bull_ob,
        'price_in_bearish_ob': price_in_bear_ob,
        'score_long': score_long,
        'score_short': score_short,
        'active_obs': all_active,
        'total_bullish': len(active_bullish),
        'total_bearish': len(active_bearish),
    }
