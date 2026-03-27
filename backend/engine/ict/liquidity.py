"""
ICT Liquidity Zones — PulseSignal Pro

Types of liquidity:
1. Buy-side liquidity (BSL): Above swing highs — stop-losses of short sellers
2. Sell-side liquidity (SSL): Below swing lows — stop-losses of long holders
3. Equal Highs (EQH): 2+ swing highs within 0.1% of each other -> BSL pool
4. Equal Lows (EQL): 2+ swing lows within 0.1% of each other -> SSL pool
5. PDH/PDL: Previous Day High/Low — major liquidity targets
6. PWH/PWL: Previous Week High/Low
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LiquidityZone:
    type: str          # 'BSL', 'SSL', 'EQH', 'EQL', 'PDH', 'PDL'
    price: float
    strength: int      # number of swing points at this level
    is_swept: bool = False       # has price taken this liquidity?
    swept_at: Optional[int] = None   # timestamp when swept
    distance_pct: float = 0.0    # % distance from current price (set after creation)


def _find_swing_highs(highs: np.ndarray, lows: np.ndarray, window: int = 3) -> list[int]:
    """Return indices of local swing highs using a left/right window."""
    result = []
    n = len(highs)
    for i in range(window, n - window):
        if all(highs[i] >= highs[i - k] for k in range(1, window + 1)) and \
           all(highs[i] >= highs[i + k] for k in range(1, window + 1)):
            result.append(i)
    return result


def _find_swing_lows(lows: np.ndarray, window: int = 3) -> list[int]:
    """Return indices of local swing lows using a left/right window."""
    result = []
    n = len(lows)
    for i in range(window, n - window):
        if all(lows[i] <= lows[i - k] for k in range(1, window + 1)) and \
           all(lows[i] <= lows[i + k] for k in range(1, window + 1)):
            result.append(i)
    return result


def detect_liquidity_zones(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    timestamps: np.ndarray,
    lookback: int = 100,
    equal_tolerance: float = 0.001,   # 0.1% tolerance for equal highs/lows
) -> dict:
    """
    Detect all liquidity zones within the lookback window.

    Swing High/Low detection uses a 3-bar pivot:
        Swing High: highs[i] is the highest in a window of 3 bars left and right.
        Swing Low:  lows[i]  is the lowest  in a window of 3 bars left and right.

    Equal Highs/Lows: two or more swing points within `equal_tolerance` of
    each other — these form dense liquidity pools.

    Liquidity sweep detection:
        Bull grab: in the last 5 candles, price briefly traded BELOW an SSL
        level (taking the stops) and then closed ABOVE that SSL level.
        Bear grab: in the last 5 candles, price briefly traded ABOVE a BSL
        level and then closed BELOW it.

    Returns:
    {
        'bsl_zones': list[LiquidityZone],
        'ssl_zones': list[LiquidityZone],
        'equal_highs': list[LiquidityZone],
        'equal_lows': list[LiquidityZone],
        'pdh': float | None,
        'pdl': float | None,
        'liquidity_grab_bull': bool,
        'liquidity_grab_bear': bool,
        'approaching_bsl': bool,
        'approaching_ssl': bool,
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
    window_start = max(0, n - lookback)

    h_slice = highs[window_start:]
    l_slice = lows[window_start:]
    c_slice = closes[window_start:]
    t_slice = timestamps[window_start:]
    slice_n = len(h_slice)

    # ── Detect swing points within the lookback window ──
    swing_window = 3
    sh_indices = _find_swing_highs(h_slice, l_slice, window=swing_window)
    sl_indices = _find_swing_lows(l_slice, window=swing_window)

    # ── Build BSL zones (above swing highs, not yet swept) ──
    bsl_zones: list[LiquidityZone] = []
    for idx in sh_indices:
        price = float(h_slice[idx])
        zone = LiquidityZone(
            type='BSL',
            price=price,
            strength=1,
            distance_pct=round((price - current_price) / current_price, 6)
            if current_price > 0 else 0.0,
        )
        # Check if swept: any subsequent high trades above this level
        for k in range(idx + 1, slice_n):
            if h_slice[k] > price:
                zone.is_swept = True
                zone.swept_at = int(t_slice[k])
                break
        bsl_zones.append(zone)

    # ── Build SSL zones (below swing lows, not yet swept) ──
    ssl_zones: list[LiquidityZone] = []
    for idx in sl_indices:
        price = float(l_slice[idx])
        zone = LiquidityZone(
            type='SSL',
            price=price,
            strength=1,
            distance_pct=round((current_price - price) / current_price, 6)
            if current_price > 0 else 0.0,
        )
        for k in range(idx + 1, slice_n):
            if l_slice[k] < price:
                zone.is_swept = True
                zone.swept_at = int(t_slice[k])
                break
        ssl_zones.append(zone)

    # ── Equal Highs / Equal Lows — cluster nearby swing points ──
    equal_highs: list[LiquidityZone] = []
    equal_lows: list[LiquidityZone] = []

    # Group BSL zones whose prices are within tolerance of each other
    processed = [False] * len(bsl_zones)
    for i in range(len(bsl_zones)):
        if processed[i]:
            continue
        cluster = [bsl_zones[i]]
        for j in range(i + 1, len(bsl_zones)):
            if processed[j]:
                continue
            ref = bsl_zones[i].price
            if abs(bsl_zones[j].price - ref) / ref <= equal_tolerance:
                cluster.append(bsl_zones[j])
                processed[j] = True
        if len(cluster) >= 2:
            avg_price = float(np.mean([z.price for z in cluster]))
            is_swept = any(z.is_swept for z in cluster)
            equal_highs.append(LiquidityZone(
                type='EQH',
                price=round(avg_price, 8),
                strength=len(cluster),
                is_swept=is_swept,
                distance_pct=round((avg_price - current_price) / current_price, 6)
                if current_price > 0 else 0.0,
            ))
        processed[i] = True

    processed = [False] * len(ssl_zones)
    for i in range(len(ssl_zones)):
        if processed[i]:
            continue
        cluster = [ssl_zones[i]]
        for j in range(i + 1, len(ssl_zones)):
            if processed[j]:
                continue
            ref = ssl_zones[i].price
            if abs(ssl_zones[j].price - ref) / ref <= equal_tolerance:
                cluster.append(ssl_zones[j])
                processed[j] = True
        if len(cluster) >= 2:
            avg_price = float(np.mean([z.price for z in cluster]))
            is_swept = any(z.is_swept for z in cluster)
            equal_lows.append(LiquidityZone(
                type='EQL',
                price=round(avg_price, 8),
                strength=len(cluster),
                is_swept=is_swept,
                distance_pct=round((current_price - avg_price) / current_price, 6)
                if current_price > 0 else 0.0,
            ))
        processed[i] = True

    # ── Previous Day High / Low (PDH / PDL) ──
    # Approximate: second-to-last 24-candle block (1H assumption)
    # The caller should ideally pass daily data; we use ~lookback/2 as a proxy
    pdh: Optional[float] = None
    pdl: Optional[float] = None
    half = max(1, lookback // 2)
    if slice_n >= half * 2:
        prev_block = h_slice[:half]
        pdh = float(np.max(prev_block))
        pdl = float(np.min(l_slice[:half]))

    # ── Active (not swept) zones for scoring ──
    active_bsl = [z for z in bsl_zones if not z.is_swept and z.price > current_price]
    active_ssl = [z for z in ssl_zones if not z.is_swept and z.price < current_price]

    # ── Liquidity grab detection (last 5 candles) ──
    look = min(5, slice_n)
    recent_highs = h_slice[-look:]
    recent_lows = l_slice[-look:]
    recent_closes = c_slice[-look:]

    # Bullish grab: price spiked below an SSL level (stop hunt), closed back above
    liquidity_grab_bull = False
    for zone in active_ssl:
        for k in range(look):
            # Candle wick went below the SSL but closed above it
            if recent_lows[k] < zone.price < recent_closes[k]:
                liquidity_grab_bull = True
                break
        if liquidity_grab_bull:
            break

    # Also check PDL sweep
    if pdl is not None and not liquidity_grab_bull:
        for k in range(look):
            if recent_lows[k] < pdl < recent_closes[k]:
                liquidity_grab_bull = True
                break

    # Bearish grab: price spiked above a BSL level then closed below
    liquidity_grab_bear = False
    for zone in active_bsl:
        for k in range(look):
            if recent_highs[k] > zone.price > recent_closes[k]:
                liquidity_grab_bear = True
                break
        if liquidity_grab_bear:
            break

    if pdh is not None and not liquidity_grab_bear:
        for k in range(look):
            if recent_highs[k] > pdh > recent_closes[k]:
                liquidity_grab_bear = True
                break

    # ── Approaching checks (within 0.5% of nearest BSL/SSL) ──
    approaching_bsl = False
    if active_bsl:
        nearest_bsl_price = min(z.price for z in active_bsl)
        approaching_bsl = (nearest_bsl_price - current_price) / current_price <= 0.005

    approaching_ssl = False
    if active_ssl:
        nearest_ssl_price = max(z.price for z in active_ssl)
        approaching_ssl = (current_price - nearest_ssl_price) / current_price <= 0.005

    # ── Scoring ──
    score_long = 0
    score_short = 0

    if liquidity_grab_bull:
        score_long = 20   # highest-probability ICT long setup
    elif approaching_ssl:
        score_long = 8

    if liquidity_grab_bear:
        score_short = 20
    elif approaching_bsl:
        score_short = 8

    # EQH/EQL confluence bonus
    eq_bsl_swept = [z for z in equal_highs if z.is_swept]
    eq_ssl_swept = [z for z in equal_lows if z.is_swept]
    if eq_ssl_swept and current_price > eq_ssl_swept[-1].price:
        score_long += 5   # SSL pool was swept, bullish continuation
    if eq_bsl_swept and current_price < eq_bsl_swept[-1].price:
        score_short += 5  # BSL pool was swept, bearish continuation

    return {
        'bsl_zones': sorted(active_bsl, key=lambda z: z.price),
        'ssl_zones': sorted(active_ssl, key=lambda z: z.price, reverse=True),
        'equal_highs': equal_highs,
        'equal_lows': equal_lows,
        'pdh': pdh,
        'pdl': pdl,
        'liquidity_grab_bull': liquidity_grab_bull,
        'liquidity_grab_bear': liquidity_grab_bear,
        'approaching_bsl': approaching_bsl,
        'approaching_ssl': approaching_ssl,
        'score_long': score_long,
        'score_short': score_short,
        'total_bsl': len(active_bsl),
        'total_ssl': len(active_ssl),
    }
