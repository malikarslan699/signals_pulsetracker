"""
Market Structure Indicators — PulseSignal Pro
Detects: HH/HL/LH/LL, BOS (Break of Structure), CHoCH (Change of Character),
         Support/Resistance zones.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class SwingPoint:
    index: int
    price: float
    type: str       # 'high' or 'low'
    timestamp: int


@dataclass
class StructureLevel:
    price: float
    type: str       # 'support' or 'resistance'
    strength: int   # number of touches
    timestamps: list = field(default_factory=list)


# ─── Swing Point Detection ────────────────────────────────────────────────────

def find_swing_points(highs: np.ndarray, lows: np.ndarray,
                      timestamps: np.ndarray, lookback: int = 5) -> dict:
    """
    Identify swing highs and lows.
    Swing high: high[i] > all highs within `lookback` bars on each side.
    Swing low:  low[i]  < all lows  within `lookback` bars on each side.
    Only candles with enough history and future bars are considered.
    """
    highs      = np.asarray(highs,      dtype=float)
    lows       = np.asarray(lows,       dtype=float)
    timestamps = np.asarray(timestamps, dtype=np.int64)
    n = len(highs)

    swing_highs: list[SwingPoint] = []
    swing_lows:  list[SwingPoint] = []

    for i in range(lookback, n - lookback):
        left_highs  = highs[i - lookback: i]
        right_highs = highs[i + 1: i + lookback + 1]
        left_lows   = lows[i - lookback: i]
        right_lows  = lows[i + 1: i + lookback + 1]

        # Skip if any NaN in the window
        if (np.any(np.isnan(left_highs)) or np.any(np.isnan(right_highs)) or
                np.any(np.isnan(left_lows)) or np.any(np.isnan(right_lows))):
            continue

        if highs[i] > np.max(left_highs) and highs[i] > np.max(right_highs):
            swing_highs.append(SwingPoint(
                index=i, price=float(highs[i]),
                type='high', timestamp=int(timestamps[i])
            ))

        if lows[i] < np.min(left_lows) and lows[i] < np.min(right_lows):
            swing_lows.append(SwingPoint(
                index=i, price=float(lows[i]),
                type='low', timestamp=int(timestamps[i])
            ))

    return {
        'swing_highs': swing_highs,
        'swing_lows':  swing_lows,
    }


# ─── Market Structure Detection ───────────────────────────────────────────────

def detect_market_structure(highs: np.ndarray, lows: np.ndarray,
                             closes: np.ndarray, timestamps: np.ndarray,
                             lookback: int = 5) -> dict:
    """
    Analyse swing sequence to determine market trend and structure events.

    Uptrend:    series of Higher Highs (HH) and Higher Lows (HL)
    Downtrend:  series of Lower Highs (LH) and Lower Lows (LL)
    Ranging:    no clear sequence

    BOS (Break of Structure):
      Bullish BOS — close breaks above last confirmed swing high.
      Bearish BOS — close breaks below last confirmed swing low.

    CHoCH (Change of Character):
      Bullish CHoCH — first HH in an established downtrend.
      Bearish CHoCH — first LL in an established uptrend.
    """
    highs      = np.asarray(highs,      dtype=float)
    lows       = np.asarray(lows,       dtype=float)
    closes     = np.asarray(closes,     dtype=float)
    timestamps = np.asarray(timestamps, dtype=np.int64)

    sp = find_swing_points(highs, lows, timestamps, lookback)
    swing_highs: list[SwingPoint] = sp['swing_highs']
    swing_lows:  list[SwingPoint] = sp['swing_lows']

    last_hh: Optional[float] = None
    last_hl: Optional[float] = None
    last_lh: Optional[float] = None
    last_ll: Optional[float] = None

    # ── Classify swing highs as HH or LH ──────────────────────────────────
    hh_list: list[float] = []
    lh_list: list[float] = []
    if len(swing_highs) >= 2:
        prev_high = swing_highs[0].price
        for sp_h in swing_highs[1:]:
            if sp_h.price > prev_high:
                hh_list.append(sp_h.price)
                last_hh = sp_h.price
            else:
                lh_list.append(sp_h.price)
                last_lh = sp_h.price
            prev_high = sp_h.price
    elif len(swing_highs) == 1:
        last_hh = swing_highs[-1].price

    # ── Classify swing lows as HL or LL ───────────────────────────────────
    hl_list: list[float] = []
    ll_list: list[float] = []
    if len(swing_lows) >= 2:
        prev_low = swing_lows[0].price
        for sp_l in swing_lows[1:]:
            if sp_l.price > prev_low:
                hl_list.append(sp_l.price)
                last_hl = sp_l.price
            else:
                ll_list.append(sp_l.price)
                last_ll = sp_l.price
            prev_low = sp_l.price
    elif len(swing_lows) == 1:
        last_ll = swing_lows[-1].price

    # ── Trend determination ────────────────────────────────────────────────
    n_hh_hl = len(hh_list) + len(hl_list)
    n_lh_ll = len(lh_list) + len(ll_list)

    if n_hh_hl >= 2 and n_hh_hl > n_lh_ll:
        trend = 'uptrend'
    elif n_lh_ll >= 2 and n_lh_ll > n_hh_hl:
        trend = 'downtrend'
    else:
        trend = 'ranging'

    close_now = closes[-1]

    # ── BOS detection ─────────────────────────────────────────────────────
    bos_bullish = False
    bos_bearish = False

    # Find most recent confirmed swing high/low (excluding the last lookback bars)
    confirmed_swing_highs = [sh for sh in swing_highs if sh.index < len(closes) - lookback]
    confirmed_swing_lows  = [sl for sl in swing_lows  if sl.index < len(closes) - lookback]

    if confirmed_swing_highs:
        last_confirmed_sh = confirmed_swing_highs[-1].price
        bos_bullish = bool(close_now > last_confirmed_sh)

    if confirmed_swing_lows:
        last_confirmed_sl = confirmed_swing_lows[-1].price
        bos_bearish = bool(close_now < last_confirmed_sl)

    # ── CHoCH detection ───────────────────────────────────────────────────
    choch_bullish = False
    choch_bearish = False

    if trend == 'downtrend' and bos_bullish:
        choch_bullish = True   # first HH in a downtrend = potential reversal

    if trend == 'uptrend' and bos_bearish:
        choch_bearish = True   # first LL in an uptrend = potential reversal

    # ── Scoring ───────────────────────────────────────────────────────────
    score_long = 0
    score_short = 0

    if trend == 'uptrend':     score_long  += 5
    if bos_bullish:            score_long  += 8
    if choch_bullish:          score_long  += 10
    if trend == 'downtrend':   score_short += 5
    if bos_bearish:            score_short += 8
    if choch_bearish:          score_short += 10

    return {
        'trend':         trend,
        'swing_highs':   swing_highs,
        'swing_lows':    swing_lows,
        'last_hh':       last_hh,
        'last_hl':       last_hl,
        'last_lh':       last_lh,
        'last_ll':       last_ll,
        'bos_bullish':   bos_bullish,
        'bos_bearish':   bos_bearish,
        'choch_bullish': choch_bullish,
        'choch_bearish': choch_bearish,
        'score_long':    score_long,
        'score_short':   score_short,
    }


# ─── Support / Resistance Detection ──────────────────────────────────────────

def _cluster_levels(prices: list[float], tolerance: float) -> list[dict]:
    """
    Merge price levels within `tolerance` * price of each other into clusters.
    Returns list of {price: centroid, count: int, raw: list}.
    """
    if not prices:
        return []

    sorted_prices = sorted(prices)
    clusters: list[dict] = []

    current_cluster = [sorted_prices[0]]
    for p in sorted_prices[1:]:
        # Use relative tolerance
        ref = np.mean(current_cluster)
        if abs(p - ref) / ref <= tolerance:
            current_cluster.append(p)
        else:
            clusters.append({
                'price': float(np.mean(current_cluster)),
                'count': len(current_cluster),
                'raw':   current_cluster[:],
            })
            current_cluster = [p]

    clusters.append({
        'price': float(np.mean(current_cluster)),
        'count': len(current_cluster),
        'raw':   current_cluster[:],
    })

    return clusters


def detect_support_resistance(highs: np.ndarray, lows: np.ndarray,
                               closes: np.ndarray, timestamps: np.ndarray,
                               zone_tolerance: float = 0.001) -> dict:
    """
    Cluster swing highs into resistance zones and swing lows into support zones.
    Zones with 2+ touches are significant.
    """
    highs      = np.asarray(highs,      dtype=float)
    lows       = np.asarray(lows,       dtype=float)
    closes     = np.asarray(closes,     dtype=float)
    timestamps = np.asarray(timestamps, dtype=np.int64)

    sp = find_swing_points(highs, lows, timestamps, lookback=5)
    swing_highs_pts: list[SwingPoint] = sp['swing_highs']
    swing_lows_pts:  list[SwingPoint] = sp['swing_lows']

    # Build resistance clusters from swing highs
    sh_prices = [pt.price for pt in swing_highs_pts]
    sl_prices = [pt.price for pt in swing_lows_pts]

    res_clusters = _cluster_levels(sh_prices, zone_tolerance)
    sup_clusters = _cluster_levels(sl_prices, zone_tolerance)

    # Build StructureLevel objects (only include zones touched 2+ times)
    resistance_zones: list[StructureLevel] = []
    for cl in res_clusters:
        if cl['count'] >= 2:
            # Find timestamps of the constituent swing points
            ts_list = [
                pt.timestamp for pt in swing_highs_pts
                if abs(pt.price - cl['price']) / cl['price'] <= zone_tolerance
            ]
            resistance_zones.append(StructureLevel(
                price=cl['price'],
                type='resistance',
                strength=cl['count'],
                timestamps=ts_list,
            ))

    support_zones: list[StructureLevel] = []
    for cl in sup_clusters:
        if cl['count'] >= 2:
            ts_list = [
                pt.timestamp for pt in swing_lows_pts
                if abs(pt.price - cl['price']) / cl['price'] <= zone_tolerance
            ]
            support_zones.append(StructureLevel(
                price=cl['price'],
                type='support',
                strength=cl['count'],
                timestamps=ts_list,
            ))

    close_now = closes[-1]

    # Nearest support/resistance
    nearest_support:    Optional[float] = None
    nearest_resistance: Optional[float] = None

    supports_below = [z.price for z in support_zones if z.price < close_now]
    resists_above  = [z.price for z in resistance_zones if z.price > close_now]

    if supports_below:
        nearest_support = max(supports_below)
    if resists_above:
        nearest_resistance = min(resists_above)

    # at_support / at_resistance: within 0.3% of nearest zone
    proximity = 0.003
    at_support    = bool(nearest_support    is not None and
                         abs(close_now - nearest_support)    / close_now <= proximity)
    at_resistance = bool(nearest_resistance is not None and
                         abs(close_now - nearest_resistance) / close_now <= proximity)

    # S/R flip: a resistance zone is now below price (acting as support) or vice versa
    sr_flip = False
    # Resistance levels that price has crossed above → now acting as support
    flipped_to_support = [z for z in resistance_zones if z.price < close_now]
    if flipped_to_support:
        top_flipped = max(z.price for z in flipped_to_support)
        if abs(close_now - top_flipped) / close_now <= proximity:
            sr_flip = True
    # Support levels that price has crossed below → now acting as resistance
    flipped_to_resistance = [z for z in support_zones if z.price > close_now]
    if flipped_to_resistance:
        bot_flipped = min(z.price for z in flipped_to_resistance)
        if abs(close_now - bot_flipped) / close_now <= proximity:
            sr_flip = True

    # Scoring
    score_long = 0
    score_short = 0
    if at_support:    score_long  += 8
    if sr_flip:       score_long  += 5
    if at_resistance: score_short += 8
    if sr_flip:       score_short += 5  # same flip can signal both; caller resolves

    return {
        'support_zones':      support_zones,
        'resistance_zones':   resistance_zones,
        'nearest_support':    nearest_support,
        'nearest_resistance': nearest_resistance,
        'at_support':         at_support,
        'at_resistance':      at_resistance,
        'sr_flip':            sr_flip,
        'score_long':         score_long,
        'score_short':        score_short,
    }
