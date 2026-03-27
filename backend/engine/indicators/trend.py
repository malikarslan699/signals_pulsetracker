"""
Trend Indicators Module — PulseSignal Pro
Implements: EMA, SMA, HMA, DEMA, TEMA, WMA, Supertrend, Ichimoku
"""
import numpy as np
import pandas as pd
from typing import Optional


# ─── EMA (Exponential Moving Average) ────────────────────────────────────────

def ema(data: np.ndarray, period: int) -> np.ndarray:
    """
    EMA using standard smoothing: k = 2/(period+1)
    Initial value = SMA of first `period` values.
    Returns array of same length as input; first (period-1) values are NaN.
    """
    data = np.asarray(data, dtype=float)
    result = np.full(len(data), np.nan)
    if len(data) < period:
        return result

    k = 2.0 / (period + 1)
    # Seed with SMA of first `period` values
    seed = np.nanmean(data[:period])
    result[period - 1] = seed
    for i in range(period, len(data)):
        if np.isnan(data[i]):
            result[i] = result[i - 1]
        else:
            result[i] = data[i] * k + result[i - 1] * (1.0 - k)
    return result


def ema_stack(closes: np.ndarray) -> dict:
    """
    Calculate EMA stack: 9, 21, 50, 100, 200.
    Returns alignment info and scoring.
    """
    closes = np.asarray(closes, dtype=float)
    e9   = ema(closes, 9)
    e21  = ema(closes, 21)
    e50  = ema(closes, 50)
    e100 = ema(closes, 100)
    e200 = ema(closes, 200)

    # Use last valid values
    def last(arr):
        valid = arr[~np.isnan(arr)]
        return valid[-1] if len(valid) > 0 else np.nan

    v9, v21, v50, v100, v200 = last(e9), last(e21), last(e50), last(e100), last(e200)

    is_bullish_stack = (
        not any(np.isnan(x) for x in [v9, v21, v50, v100, v200])
        and v9 > v21 > v50 > v100 > v200
    )
    is_bearish_stack = (
        not any(np.isnan(x) for x in [v9, v21, v50, v100, v200])
        and v9 < v21 < v50 < v100 < v200
    )

    # Count how many consecutive pairs are in bullish order
    vals = [v9, v21, v50, v100, v200]
    bullish_count = 0
    for i in range(len(vals) - 1):
        if not np.isnan(vals[i]) and not np.isnan(vals[i + 1]) and vals[i] > vals[i + 1]:
            bullish_count += 1
        else:
            break

    if is_bullish_stack:
        score = 10
    elif bullish_count >= 3:
        score = 5
    else:
        score = 0

    return {
        'ema9':   e9,
        'ema21':  e21,
        'ema50':  e50,
        'ema100': e100,
        'ema200': e200,
        'is_bullish_stack': is_bullish_stack,
        'is_bearish_stack': is_bearish_stack,
        'bullish_count': bullish_count,
        'score': score,
    }


# ─── SMA (Simple Moving Average) ─────────────────────────────────────────────

def sma(data: np.ndarray, period: int) -> np.ndarray:
    """
    Simple moving average using uniform convolution.
    First (period-1) values are NaN.
    """
    data = np.asarray(data, dtype=float)
    result = np.full(len(data), np.nan)
    if len(data) < period:
        return result
    kernel = np.ones(period) / period
    # Use pandas rolling for NaN-aware SMA
    s = pd.Series(data)
    rolled = s.rolling(period).mean().to_numpy()
    return rolled


def sma_cross(closes: np.ndarray, fast: int = 7, slow: int = 25) -> dict:
    """
    SMA crossover analysis.
    Golden cross: fast just crossed above slow.
    Death cross:  fast just crossed below slow.
    """
    closes = np.asarray(closes, dtype=float)
    fast_sma = sma(closes, fast)
    slow_sma = sma(closes, slow)

    is_golden_cross = False
    is_death_cross  = False
    direction = 'neutral'
    score = 0

    # Need at least 2 valid values to detect a cross
    valid_mask = ~(np.isnan(fast_sma) | np.isnan(slow_sma))
    valid_idx  = np.where(valid_mask)[0]

    if len(valid_idx) >= 2:
        i_last = valid_idx[-1]
        i_prev = valid_idx[-2]

        prev_diff = fast_sma[i_prev] - slow_sma[i_prev]
        curr_diff = fast_sma[i_last] - slow_sma[i_last]

        if prev_diff <= 0 and curr_diff > 0:
            is_golden_cross = True
            direction = 'bull'
            score = 8
        elif prev_diff >= 0 and curr_diff < 0:
            is_death_cross = True
            direction = 'bear'
            score = -8
        elif curr_diff > 0:
            direction = 'bull'
        elif curr_diff < 0:
            direction = 'bear'

    return {
        'fast':             fast_sma,
        'slow':             slow_sma,
        'is_golden_cross':  is_golden_cross,
        'is_death_cross':   is_death_cross,
        'direction':        direction,
        'score':            score,
    }


# ─── WMA (Weighted Moving Average) ───────────────────────────────────────────

def wma(data: np.ndarray, period: int) -> np.ndarray:
    """
    Linearly weighted moving average.
    Weights: 1, 2, 3, ..., period (most recent = highest weight).
    First (period-1) values are NaN.
    """
    data = np.asarray(data, dtype=float)
    result = np.full(len(data), np.nan)
    if len(data) < period:
        return result

    weights = np.arange(1, period + 1, dtype=float)
    weight_sum = weights.sum()

    for i in range(period - 1, len(data)):
        window = data[i - period + 1: i + 1]
        if np.any(np.isnan(window)):
            result[i] = np.nan
        else:
            result[i] = np.dot(window, weights) / weight_sum
    return result


# ─── HMA (Hull Moving Average) ────────────────────────────────────────────────

def hma(data: np.ndarray, period: int = 14) -> np.ndarray:
    """
    HMA = WMA(2*WMA(n/2) - WMA(n), sqrt(n))
    Reduces lag while maintaining smoothness.
    """
    data = np.asarray(data, dtype=float)
    half_period = max(2, period // 2)
    sqrt_period = max(2, int(round(np.sqrt(period))))

    wma_half = wma(data, half_period)
    wma_full = wma(data, period)

    # Raw HMA series
    diff = 2.0 * wma_half - wma_full
    result = wma(diff, sqrt_period)
    return result


def hma_direction(closes: np.ndarray, period: int = 14) -> dict:
    """
    HMA direction analysis.
    is_rising: current HMA > previous HMA.
    direction_changed: direction changed in last 3 candles.
    """
    closes = np.asarray(closes, dtype=float)
    h = hma(closes, period)

    valid_idx = np.where(~np.isnan(h))[0]
    is_rising = False
    direction_changed = False
    score = 0

    if len(valid_idx) >= 2:
        is_rising = h[valid_idx[-1]] > h[valid_idx[-2]]
        score = 6 if is_rising else -6

    if len(valid_idx) >= 3:
        # Check if direction changed within the last 3 valid candles
        last3 = h[valid_idx[-3:]]
        diffs = np.diff(last3)
        signs = np.sign(diffs)
        # direction_changed if signs flipped
        if len(signs) >= 2 and signs[0] != signs[1] and signs[1] != 0:
            direction_changed = True

    return {
        'hma':               h,
        'is_rising':         is_rising,
        'direction_changed': direction_changed,
        'score':             score,
    }


# ─── DEMA / TEMA ──────────────────────────────────────────────────────────────

def dema(data: np.ndarray, period: int) -> np.ndarray:
    """
    Double Exponential Moving Average.
    DEMA = 2 * EMA(n) - EMA(EMA(n))
    Reduces lag compared to standard EMA.
    """
    data = np.asarray(data, dtype=float)
    e1 = ema(data, period)
    e2 = ema(e1, period)
    result = 2.0 * e1 - e2
    # Where either is NaN, result should be NaN
    result[np.isnan(e1) | np.isnan(e2)] = np.nan
    return result


def tema(data: np.ndarray, period: int) -> np.ndarray:
    """
    Triple Exponential Moving Average.
    TEMA = 3*EMA(n) - 3*EMA(EMA(n)) + EMA(EMA(EMA(n)))
    """
    data = np.asarray(data, dtype=float)
    e1 = ema(data, period)
    e2 = ema(e1, period)
    e3 = ema(e2, period)
    result = 3.0 * e1 - 3.0 * e2 + e3
    result[np.isnan(e1) | np.isnan(e2) | np.isnan(e3)] = np.nan
    return result


# ─── Supertrend ───────────────────────────────────────────────────────────────

def _wilder_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                period: int) -> np.ndarray:
    """Internal Wilder's ATR used by Supertrend."""
    highs  = np.asarray(highs,  dtype=float)
    lows   = np.asarray(lows,   dtype=float)
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    tr = np.full(n, np.nan)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        hl  = highs[i] - lows[i]
        hpc = abs(highs[i]  - closes[i - 1])
        lpc = abs(lows[i]   - closes[i - 1])
        tr[i] = max(hl, hpc, lpc)

    atr_arr = np.full(n, np.nan)
    if n < period:
        return atr_arr
    # Seed with simple average
    atr_arr[period - 1] = np.mean(tr[1:period])  # exclude index 0 (no prev close)
    for i in range(period, n):
        atr_arr[i] = (atr_arr[i - 1] * (period - 1) + tr[i]) / period
    return atr_arr


def supertrend(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
               period: int = 10, multiplier: float = 3.0) -> dict:
    """
    Supertrend indicator using ATR bands.
    Upper Band = (H+L)/2 + multiplier * ATR
    Lower Band = (H+L)/2 - multiplier * ATR
    Direction flips when close crosses the active band.
    """
    highs  = np.asarray(highs,  dtype=float)
    lows   = np.asarray(lows,   dtype=float)
    closes = np.asarray(closes, dtype=float)
    n = len(closes)

    atr_vals = _wilder_atr(highs, lows, closes, period)

    hl2 = (highs + lows) / 2.0
    basic_upper = hl2 + multiplier * atr_vals
    basic_lower = hl2 - multiplier * atr_vals

    final_upper = np.full(n, np.nan)
    final_lower = np.full(n, np.nan)
    supertrend_arr = np.full(n, np.nan)
    direction_arr  = np.zeros(n, dtype=int)  # 1 = bull, -1 = bear

    # Find first non-NaN ATR index
    start = period - 1
    if start >= n:
        return {
            'supertrend':   supertrend_arr,
            'direction':    direction_arr,
            'is_bullish':   False,
            'is_bearish':   False,
            'just_flipped': False,
            'score':        0,
        }

    final_upper[start] = basic_upper[start]
    final_lower[start] = basic_lower[start]
    direction_arr[start] = 1  # default start bullish

    for i in range(start + 1, n):
        if np.isnan(atr_vals[i]):
            final_upper[i] = final_upper[i - 1]
            final_lower[i] = final_lower[i - 1]
            direction_arr[i] = direction_arr[i - 1]
            continue

        # Final upper: only tighten (lower) if prev close was below prev upper
        if basic_upper[i] < final_upper[i - 1] or closes[i - 1] > final_upper[i - 1]:
            final_upper[i] = basic_upper[i]
        else:
            final_upper[i] = final_upper[i - 1]

        # Final lower: only tighten (raise) if prev close was above prev lower
        if basic_lower[i] > final_lower[i - 1] or closes[i - 1] < final_lower[i - 1]:
            final_lower[i] = basic_lower[i]
        else:
            final_lower[i] = final_lower[i - 1]

        # Determine direction
        prev_dir = direction_arr[i - 1]
        if prev_dir == -1 and closes[i] > final_upper[i]:
            direction_arr[i] = 1
        elif prev_dir == 1 and closes[i] < final_lower[i]:
            direction_arr[i] = -1
        else:
            direction_arr[i] = prev_dir

        supertrend_arr[i] = final_lower[i] if direction_arr[i] == 1 else final_upper[i]

    supertrend_arr[start] = final_lower[start] if direction_arr[start] == 1 else final_upper[start]

    # Current state
    is_bullish   = bool(direction_arr[-1] == 1)
    is_bearish   = bool(direction_arr[-1] == -1)
    just_flipped = False
    if n >= 2:
        just_flipped = bool(direction_arr[-1] != direction_arr[-2])

    if just_flipped:
        score = 15 if is_bullish else -15
    elif is_bullish:
        score = 10
    elif is_bearish:
        score = -10
    else:
        score = 0

    return {
        'supertrend':   supertrend_arr,
        'direction':    direction_arr,
        'is_bullish':   is_bullish,
        'is_bearish':   is_bearish,
        'just_flipped': just_flipped,
        'score':        score,
    }


# ─── Ichimoku Cloud ───────────────────────────────────────────────────────────

def _midpoint(highs: np.ndarray, lows: np.ndarray, period: int) -> np.ndarray:
    """Rolling (highest_high + lowest_low) / 2 over `period`."""
    n = len(highs)
    result = np.full(n, np.nan)
    for i in range(period - 1, n):
        result[i] = (np.max(highs[i - period + 1: i + 1]) +
                     np.min(lows[i  - period + 1: i + 1])) / 2.0
    return result


def ichimoku(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
             tenkan_period: int = 9, kijun_period: int = 26,
             senkou_b_period: int = 52) -> dict:
    """
    Ichimoku Kinko Hyo indicator.
    Tenkan-sen  = midpoint over tenkan_period
    Kijun-sen   = midpoint over kijun_period
    Senkou A    = (Tenkan + Kijun) / 2, shifted forward by kijun_period
    Senkou B    = midpoint over senkou_b_period, shifted forward by kijun_period
    Chikou      = Close shifted back by kijun_period
    """
    highs  = np.asarray(highs,  dtype=float)
    lows   = np.asarray(lows,   dtype=float)
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    shift = kijun_period

    tenkan = _midpoint(highs, lows, tenkan_period)
    kijun  = _midpoint(highs, lows, kijun_period)
    senkou_b_raw = _midpoint(highs, lows, senkou_b_period)

    # Senkou A (future cloud, shifted forward)
    senkou_a = np.full(n + shift, np.nan)
    span_a_raw = (tenkan + kijun) / 2.0
    senkou_a[shift:] = span_a_raw

    senkou_b = np.full(n + shift, np.nan)
    senkou_b[shift:] = senkou_b_raw

    # Trim/pad to length n for current-candle analysis
    senkou_a_current = senkou_a[:n]
    senkou_b_current = senkou_b[:n]

    # Chikou = close shifted back by `shift` periods (plot at -26)
    chikou = np.full(n, np.nan)
    chikou[:n - shift] = closes[shift:]

    # ── Current-state analysis ──────────────────────────────────────────────
    close_now = closes[-1]

    def _last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return valid[-1] if len(valid) else np.nan

    sa_now = _last_valid(senkou_a_current)
    sb_now = _last_valid(senkou_b_current)
    tk_now = _last_valid(tenkan)
    kj_now = _last_valid(kijun)

    above_cloud = False
    below_cloud = False
    in_cloud    = False
    cloud_bullish = False

    if not np.isnan(sa_now) and not np.isnan(sb_now):
        cloud_top    = max(sa_now, sb_now)
        cloud_bottom = min(sa_now, sb_now)
        above_cloud  = bool(close_now > cloud_top)
        below_cloud  = bool(close_now < cloud_bottom)
        in_cloud     = bool(cloud_bottom <= close_now <= cloud_top)
        cloud_bullish = bool(sa_now > sb_now)

    # TK cross: tenkan crossed above kijun on last candle
    tk_cross_bull = False
    valid_tk = ~np.isnan(tenkan)
    valid_kj = ~np.isnan(kijun)
    both_valid = valid_tk & valid_kj
    both_idx = np.where(both_valid)[0]
    if len(both_idx) >= 2:
        i_last = both_idx[-1]
        i_prev = both_idx[-2]
        tk_cross_bull = bool(
            tenkan[i_prev] <= kijun[i_prev] and tenkan[i_last] > kijun[i_last]
        )

    # Chikou confirms: chikou > price 26 bars ago
    chikou_confirms = False
    if n > shift:
        chikou_val = closes[-1 - shift] if (n - 1 - shift) >= 0 else np.nan
        ref_price  = closes[-1 - shift] if (n - 1 - shift) >= 0 else np.nan
        # Chikou is the close from 26 bars ago plotted today
        # It "confirms" if close[n-26] > close[n-26-1] area — standard: chikou above price 26 ago
        if n >= shift * 2:
            chikou_confirms = bool(closes[n - 1 - shift] > closes[n - 1 - shift * 2])

    # Scoring (up to +17)
    score = 0
    if above_cloud:
        score += 5
    if cloud_bullish:
        score += 3
    if tk_cross_bull:
        score += 5
    if chikou_confirms:
        score += 4

    return {
        'tenkan':           tenkan,
        'kijun':            kijun,
        'senkou_a':         senkou_a,
        'senkou_b':         senkou_b,
        'chikou':           chikou,
        'above_cloud':      above_cloud,
        'below_cloud':      below_cloud,
        'in_cloud':         in_cloud,
        'cloud_bullish':    cloud_bullish,
        'tk_cross_bull':    tk_cross_bull,
        'chikou_confirms':  chikou_confirms,
        'score':            score,
    }
