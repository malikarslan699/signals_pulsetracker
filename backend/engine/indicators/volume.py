"""
Volume Indicators Module — PulseSignal Pro
Implements: Volume Spike, OBV, VWAP, CMF, VROC
"""
import numpy as np
import pandas as pd
from typing import Optional


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _ema(data: np.ndarray, period: int) -> np.ndarray:
    """EMA seeded with SMA, k = 2/(period+1). NaN-safe."""
    data = np.asarray(data, dtype=float)
    result = np.full(len(data), np.nan)
    if len(data) < period:
        return result

    # Find first contiguous window without NaN
    for start in range(len(data) - period + 1):
        window = data[start: start + period]
        if not np.any(np.isnan(window)):
            break
    else:
        return result

    k = 2.0 / (period + 1)
    result[start + period - 1] = np.mean(data[start: start + period])
    for i in range(start + period, len(data)):
        if np.isnan(data[i]):
            result[i] = result[i - 1]
        else:
            result[i] = data[i] * k + result[i - 1] * (1.0 - k)
    return result


def _sma(data: np.ndarray, period: int) -> np.ndarray:
    s = pd.Series(np.asarray(data, dtype=float))
    return s.rolling(period).mean().to_numpy()


def _find_swing_highs(arr: np.ndarray, left: int = 3, right: int = 3):
    n = len(arr)
    indices = []
    for i in range(left, n - right):
        window = arr[i - left: i + right + 1]
        if np.any(np.isnan(window)):
            continue
        if arr[i] == np.max(window):
            indices.append(i)
    return np.array(indices, dtype=int)


def _find_swing_lows(arr: np.ndarray, left: int = 3, right: int = 3):
    n = len(arr)
    indices = []
    for i in range(left, n - right):
        window = arr[i - left: i + right + 1]
        if np.any(np.isnan(window)):
            continue
        if arr[i] == np.min(window):
            indices.append(i)
    return np.array(indices, dtype=int)


def _detect_divergence(price: np.ndarray, indicator: np.ndarray, lookback: int = 20):
    """Returns (bullish_div, bearish_div)."""
    n = len(price)
    if n < lookback + 6:
        return False, False

    p_slice   = price[n - lookback:]
    ind_slice = indicator[n - lookback:]

    if np.any(np.isnan(ind_slice)):
        ind_slice = pd.Series(ind_slice).ffill().to_numpy()

    p_lows   = _find_swing_lows(p_slice,  2, 2)
    i_lows   = _find_swing_lows(ind_slice, 2, 2)
    p_highs  = _find_swing_highs(p_slice,  2, 2)
    i_highs  = _find_swing_highs(ind_slice, 2, 2)

    bullish_div = False
    if len(p_lows) >= 2 and len(i_lows) >= 2:
        pl1, pl2 = p_lows[-2], p_lows[-1]
        il1, il2 = i_lows[-2], i_lows[-1]
        if p_slice[pl2] < p_slice[pl1] and ind_slice[il2] > ind_slice[il1]:
            bullish_div = True

    bearish_div = False
    if len(p_highs) >= 2 and len(i_highs) >= 2:
        ph1, ph2 = p_highs[-2], p_highs[-1]
        ih1, ih2 = i_highs[-2], i_highs[-1]
        if p_slice[ph2] > p_slice[ph1] and ind_slice[ih2] < ind_slice[ih1]:
            bearish_div = True

    return bullish_div, bearish_div


# ─── Volume Spike ────────────────────────────────────────────────────────────

def volume_spike(volumes: np.ndarray, period: int = 20,
                 threshold: float = 2.0) -> dict:
    """
    avg_volume = SMA(volume, period)
    spike      = current_volume > threshold * avg_volume
    """
    volumes = np.asarray(volumes, dtype=float)
    avg_vol_arr = _sma(volumes, period)

    def last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if len(valid) else np.nan

    avg_vol  = last_valid(avg_vol_arr)
    curr_vol = float(volumes[-1]) if len(volumes) > 0 else np.nan

    if np.isnan(avg_vol) or avg_vol == 0 or np.isnan(curr_vol):
        vol_ratio      = np.nan
        is_spike       = False
        spike_strength = np.nan
        score = 0
    else:
        vol_ratio      = curr_vol / avg_vol
        is_spike       = bool(curr_vol > threshold * avg_vol)
        spike_strength = vol_ratio

        if curr_vol > 3.0 * avg_vol:
            score = 12
        elif is_spike:
            score = 8
        else:
            score = 0

    return {
        'avg_volume':     avg_vol,
        'current_volume': curr_vol,
        'volume_ratio':   vol_ratio,
        'is_spike':       is_spike,
        'spike_strength': spike_strength,
        'score':          score,
    }


# ─── OBV (On-Balance Volume) ─────────────────────────────────────────────────

def obv(closes: np.ndarray, volumes: np.ndarray) -> dict:
    """
    OBV: if close > prev_close → OBV += volume
         if close < prev_close → OBV -= volume
         else                  → OBV unchanged
    """
    closes  = np.asarray(closes,  dtype=float)
    volumes = np.asarray(volumes, dtype=float)
    n = len(closes)

    obv_arr = np.zeros(n, dtype=float)
    obv_arr[0] = volumes[0]
    for i in range(1, n):
        if closes[i] > closes[i - 1]:
            obv_arr[i] = obv_arr[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            obv_arr[i] = obv_arr[i - 1] - volumes[i]
        else:
            obv_arr[i] = obv_arr[i - 1]

    obv_ema = _ema(obv_arr, 20)

    # Trend: OBV above/below its EMA
    trend = 'neutral'
    valid_ema = obv_ema[~np.isnan(obv_ema)]
    if len(valid_ema) >= 1:
        obv_now = obv_arr[-1]
        ema_now = valid_ema[-1]
        if obv_now > ema_now:
            trend = 'bull'
        elif obv_now < ema_now:
            trend = 'bear'

    bull_div, bear_div = _detect_divergence(closes, obv_arr, 20)

    score_long = 0
    score_short = 0
    if trend == 'bull':  score_long  += 5
    if bull_div:         score_long  += 7
    if trend == 'bear':  score_short += 5
    if bear_div:         score_short += 7

    return {
        'obv':                obv_arr,
        'obv_ema':            obv_ema,
        'trend':              trend,
        'bullish_divergence': bull_div,
        'bearish_divergence': bear_div,
        'score_long':         score_long,
        'score_short':        score_short,
    }


# ─── VWAP (Volume Weighted Average Price) ────────────────────────────────────

def vwap(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
         volumes: np.ndarray) -> dict:
    """
    Typical Price = (H+L+C)/3
    VWAP = cumsum(TP * Volume) / cumsum(Volume)
    Bands at ±1σ and ±2σ using cumulative standard deviation.
    """
    highs   = np.asarray(highs,   dtype=float)
    lows    = np.asarray(lows,    dtype=float)
    closes  = np.asarray(closes,  dtype=float)
    volumes = np.asarray(volumes, dtype=float)
    n = len(closes)

    tp = (highs + lows + closes) / 3.0

    cum_tp_vol = np.cumsum(tp * volumes)
    cum_vol    = np.cumsum(volumes)

    with np.errstate(invalid='ignore', divide='ignore'):
        vwap_arr = np.where(cum_vol > 0, cum_tp_vol / cum_vol, np.nan)

    # Cumulative variance for bands
    # Var_cum = sum(vol*(tp - vwap)^2) / sum(vol)
    cum_sq_dev_vol = np.cumsum(volumes * (tp - vwap_arr) ** 2)
    with np.errstate(invalid='ignore', divide='ignore'):
        cum_var = np.where(cum_vol > 0, cum_sq_dev_vol / cum_vol, np.nan)
    cum_std = np.sqrt(np.maximum(cum_var, 0.0))

    upper_1 = vwap_arr + 1.0 * cum_std
    upper_2 = vwap_arr + 2.0 * cum_std
    lower_1 = vwap_arr - 1.0 * cum_std
    lower_2 = vwap_arr - 2.0 * cum_std

    def last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if len(valid) else np.nan

    vwap_cur = last_valid(vwap_arr)
    close_now = closes[-1]

    if np.isnan(vwap_cur):
        price_vs_vwap = 'unknown'
    elif abs(close_now - vwap_cur) / vwap_cur < 0.001:
        price_vs_vwap = 'at'
    elif close_now > vwap_cur:
        price_vs_vwap = 'above'
    else:
        price_vs_vwap = 'below'

    # Cross detection
    crossed_above = False
    crossed_below = False
    valid_vwap = vwap_arr[~np.isnan(vwap_arr)]
    if len(valid_vwap) >= 2 and n >= 2:
        vwap_prev = valid_vwap[-2]
        vwap_curr = valid_vwap[-1]
        close_prev = closes[-2]
        close_curr = closes[-1]
        crossed_above = bool(close_prev <= vwap_prev and close_curr > vwap_curr)
        crossed_below = bool(close_prev >= vwap_prev and close_curr < vwap_curr)

    # Bounce: price touched lower_1 and bounced back above VWAP within 3 candles
    bounce_at_vwap = False
    if n >= 3:
        l1_slice = lower_1[n - 3: n]
        v_slice  = vwap_arr[n - 3: n]
        c_slice  = closes[n - 3: n]
        if not np.any(np.isnan(l1_slice)) and not np.any(np.isnan(v_slice)):
            touched_lower = np.any(c_slice <= l1_slice)
            ends_above    = c_slice[-1] > v_slice[-1]
            bounce_at_vwap = bool(touched_lower and ends_above)

    score_long = 0
    score_short = 0
    if price_vs_vwap == 'above':   score_long  += 5
    if crossed_above:              score_long  += 7
    if bounce_at_vwap:             score_long  += 6
    if price_vs_vwap == 'below':   score_short += 5
    if crossed_below:              score_short += 7

    return {
        'vwap':          vwap_arr,
        'upper_1':       upper_1,
        'upper_2':       upper_2,
        'lower_1':       lower_1,
        'lower_2':       lower_2,
        'current_vwap':  vwap_cur,
        'price_vs_vwap': price_vs_vwap,
        'crossed_above': crossed_above,
        'crossed_below': crossed_below,
        'bounce_at_vwap': bounce_at_vwap,
        'score_long':    score_long,
        'score_short':   score_short,
    }


# ─── CMF (Chaikin Money Flow) ─────────────────────────────────────────────────

def cmf(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
        volumes: np.ndarray, period: int = 20) -> dict:
    """
    Money Flow Multiplier = ((Close-Low) - (High-Close)) / (High-Low)
    Money Flow Volume     = MFM * Volume
    CMF = sum(MFV, period) / sum(Volume, period)
    """
    highs   = np.asarray(highs,   dtype=float)
    lows    = np.asarray(lows,    dtype=float)
    closes  = np.asarray(closes,  dtype=float)
    volumes = np.asarray(volumes, dtype=float)
    n = len(closes)

    hl = highs - lows
    with np.errstate(invalid='ignore', divide='ignore'):
        mfm = np.where(hl != 0,
                       ((closes - lows) - (highs - closes)) / hl,
                       0.0)
    mfv = mfm * volumes

    cmf_arr = np.full(n, np.nan)
    for i in range(period - 1, n):
        vol_sum = np.sum(volumes[i - period + 1: i + 1])
        if vol_sum == 0:
            cmf_arr[i] = 0.0
        else:
            cmf_arr[i] = np.sum(mfv[i - period + 1: i + 1]) / vol_sum

    def last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if len(valid) else np.nan

    current = last_valid(cmf_arr)

    is_positive    = bool(not np.isnan(current) and current > 0.1)
    is_negative    = bool(not np.isnan(current) and current < -0.1)
    is_strong_bull = bool(not np.isnan(current) and current > 0.2)
    is_strong_bear = bool(not np.isnan(current) and current < -0.2)

    score_long = 0
    score_short = 0
    if is_positive:    score_long  += 4
    if is_strong_bull: score_long  += 5
    if is_negative:    score_short += 4
    if is_strong_bear: score_short += 5

    return {
        'cmf':            cmf_arr,
        'current':        current,
        'is_positive':    is_positive,
        'is_negative':    is_negative,
        'is_strong_bull': is_strong_bull,
        'is_strong_bear': is_strong_bear,
        'score_long':     score_long,
        'score_short':    score_short,
    }


# ─── VROC (Volume Rate of Change) ─────────────────────────────────────────────

def vroc(volumes: np.ndarray, period: int = 14) -> dict:
    """
    VROC = (Volume - Volume[n]) / Volume[n] * 100
    Measures how much current volume has changed versus n periods ago.
    """
    volumes = np.asarray(volumes, dtype=float)
    n = len(volumes)

    vroc_arr = np.full(n, np.nan)
    for i in range(period, n):
        prev = volumes[i - period]
        if prev != 0 and not np.isnan(prev):
            vroc_arr[i] = (volumes[i] - prev) / prev * 100.0

    def last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if len(valid) else np.nan

    current = last_valid(vroc_arr)

    # Rising volume: last 3 valid values trend upward
    rising_volume = False
    valid_vroc = vroc_arr[~np.isnan(vroc_arr)]
    if len(valid_vroc) >= 3:
        rising_volume = bool(valid_vroc[-1] > valid_vroc[-2] > valid_vroc[-3])

    score = 0
    if not np.isnan(current):
        if current > 50 and rising_volume:
            score = 7
        elif current > 25:
            score = 4
        elif current > 0:
            score = 2

    return {
        'vroc':          vroc_arr,
        'current':       current,
        'rising_volume': rising_volume,
        'score':         score,
    }
