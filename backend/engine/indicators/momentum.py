"""
Momentum Indicators Module — PulseSignal Pro
Implements: RSI, Stochastic RSI, MACD, CCI, Williams %R, ROC, MFI
"""
import numpy as np
import pandas as pd
from typing import Optional


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _ema(data: np.ndarray, period: int) -> np.ndarray:
    """Internal EMA helper (k = 2/(period+1)), seeded with SMA."""
    data = np.asarray(data, dtype=float)
    result = np.full(len(data), np.nan)
    if len(data) < period:
        return result
    k = 2.0 / (period + 1)
    # Find first non-NaN seed
    seed_vals = data[:period]
    if np.any(np.isnan(seed_vals)):
        return result
    result[period - 1] = np.mean(seed_vals)
    for i in range(period, len(data)):
        if np.isnan(data[i]):
            result[i] = result[i - 1]
        else:
            result[i] = data[i] * k + result[i - 1] * (1.0 - k)
    return result


def _sma(data: np.ndarray, period: int) -> np.ndarray:
    """Internal SMA helper."""
    s = pd.Series(np.asarray(data, dtype=float))
    return s.rolling(period).mean().to_numpy()


def _find_swing_highs(arr: np.ndarray, left: int = 3, right: int = 3) -> np.ndarray:
    """Return indices where arr[i] is a local maximum (left/right bars on each side)."""
    n = len(arr)
    indices = []
    for i in range(left, n - right):
        window_l = arr[i - left: i]
        window_r = arr[i + 1: i + right + 1]
        if not np.any(np.isnan(arr[i - left: i + right + 1])):
            if arr[i] == np.max(arr[i - left: i + right + 1]):
                indices.append(i)
    return np.array(indices, dtype=int)


def _find_swing_lows(arr: np.ndarray, left: int = 3, right: int = 3) -> np.ndarray:
    """Return indices where arr[i] is a local minimum."""
    n = len(arr)
    indices = []
    for i in range(left, n - right):
        if not np.any(np.isnan(arr[i - left: i + right + 1])):
            if arr[i] == np.min(arr[i - left: i + right + 1]):
                indices.append(i)
    return np.array(indices, dtype=int)


def _detect_divergence(price: np.ndarray, indicator: np.ndarray,
                        lookback: int = 20):
    """
    Detect bullish/bearish divergence over last `lookback` candles.
    Bullish:  price makes lower low, indicator makes higher low.
    Bearish:  price makes higher high, indicator makes lower high.
    Returns (bullish_div, bearish_div) booleans.
    """
    n = len(price)
    if n < lookback + 6:
        return False, False

    p_slice   = price[n - lookback:]
    ind_slice = indicator[n - lookback:]

    if np.any(np.isnan(ind_slice)):
        ind_slice = pd.Series(ind_slice).ffill().to_numpy()

    # Swing lows (for bullish divergence)
    p_lows  = _find_swing_lows(p_slice, 2, 2)
    i_lows  = _find_swing_lows(ind_slice, 2, 2)

    # Swing highs (for bearish divergence)
    p_highs = _find_swing_highs(p_slice, 2, 2)
    i_highs = _find_swing_highs(ind_slice, 2, 2)

    bullish_div = False
    if len(p_lows) >= 2 and len(i_lows) >= 2:
        pl1, pl2 = p_lows[-2], p_lows[-1]
        il1, il2 = i_lows[-2], i_lows[-1]
        # Price lower low, indicator higher low
        if p_slice[pl2] < p_slice[pl1] and ind_slice[il2] > ind_slice[il1]:
            bullish_div = True

    bearish_div = False
    if len(p_highs) >= 2 and len(i_highs) >= 2:
        ph1, ph2 = p_highs[-2], p_highs[-1]
        ih1, ih2 = i_highs[-2], i_highs[-1]
        # Price higher high, indicator lower high
        if p_slice[ph2] > p_slice[ph1] and ind_slice[ih2] < ind_slice[ih1]:
            bearish_div = True

    return bullish_div, bearish_div


# ─── RSI ──────────────────────────────────────────────────────────────────────

def rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """
    RSI using Wilder's Smoothed Moving Average (SMMA / RMA).
    RS = smma_gain / smma_loss
    RSI = 100 - 100 / (1 + RS)
    First `period` values are NaN.
    """
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    result = np.full(n, np.nan)
    if n < period + 1:
        return result

    deltas = np.diff(closes)
    gains  = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    # Seed: simple average of first `period` gains/losses
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    for i in range(period, n):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        if avg_loss == 0.0:
            result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100.0 - 100.0 / (1.0 + rs)

    return result


def rsi_analysis(closes: np.ndarray) -> dict:
    """
    Run RSI(6) fast and RSI(14) standard with full analysis.
    Divergence detection over last 20 candles.
    """
    closes = np.asarray(closes, dtype=float)

    rsi14 = rsi(closes, 14)
    rsi6  = rsi(closes, 6)

    def last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if len(valid) else np.nan

    rsi14_cur = last_valid(rsi14)
    rsi6_cur  = last_valid(rsi6)

    is_oversold           = bool(not np.isnan(rsi14_cur) and rsi14_cur < 30)
    is_overbought         = bool(not np.isnan(rsi14_cur) and rsi14_cur > 70)
    is_extreme_oversold   = bool(not np.isnan(rsi6_cur)  and rsi6_cur < 20)
    is_extreme_overbought = bool(not np.isnan(rsi6_cur)  and rsi6_cur > 80)

    bull_div, bear_div = _detect_divergence(closes, rsi14, 20)

    # Scoring
    score_long = 0
    score_short = 0
    if is_oversold:           score_long  += 6
    if is_extreme_oversold:   score_long  += 4
    if bull_div:              score_long  += 8
    if is_overbought:         score_short += 6
    if is_extreme_overbought: score_short += 4
    if bear_div:              score_short += 8

    return {
        'rsi14':                  rsi14,
        'rsi6':                   rsi6,
        'rsi14_current':          rsi14_cur,
        'rsi6_current':           rsi6_cur,
        'is_oversold':            is_oversold,
        'is_overbought':          is_overbought,
        'is_extreme_oversold':    is_extreme_oversold,
        'is_extreme_overbought':  is_extreme_overbought,
        'bullish_divergence':     bull_div,
        'bearish_divergence':     bear_div,
        'score_long':             score_long,
        'score_short':            score_short,
    }


# ─── Stochastic RSI ───────────────────────────────────────────────────────────

def stochastic_rsi(closes: np.ndarray, rsi_period: int = 14,
                   stoch_period: int = 14, k_period: int = 3,
                   d_period: int = 3) -> dict:
    """
    StochRSI = (RSI - lowest_RSI_n) / (highest_RSI_n - lowest_RSI_n)
    %K = SMA(StochRSI, k_period)
    %D = SMA(%K, d_period)
    All values scaled 0–100.
    """
    closes = np.asarray(closes, dtype=float)
    rsi_vals = rsi(closes, rsi_period)

    n = len(rsi_vals)
    stoch_rsi = np.full(n, np.nan)

    for i in range(stoch_period - 1, n):
        window = rsi_vals[i - stoch_period + 1: i + 1]
        if np.any(np.isnan(window)):
            continue
        lo = np.min(window)
        hi = np.max(window)
        denom = hi - lo
        stoch_rsi[i] = 0.0 if denom == 0 else (rsi_vals[i] - lo) / denom * 100.0

    k = _sma(stoch_rsi, k_period)
    d = _sma(k, d_period)

    def last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if len(valid) else np.nan

    k_cur = last_valid(k)
    d_cur = last_valid(d)

    is_oversold  = bool(not np.isnan(k_cur) and k_cur < 20)
    is_overbought = bool(not np.isnan(k_cur) and k_cur > 80)

    # Cross detection
    bull_cross = False
    bear_cross = False
    valid_both = ~(np.isnan(k) | np.isnan(d))
    valid_idx  = np.where(valid_both)[0]
    if len(valid_idx) >= 2:
        i_last = valid_idx[-1]
        i_prev = valid_idx[-2]
        prev_diff = k[i_prev] - d[i_prev]
        curr_diff = k[i_last] - d[i_last]
        if prev_diff <= 0 and curr_diff > 0 and k[i_last] < 20:
            bull_cross = True
        if prev_diff >= 0 and curr_diff < 0 and k[i_last] > 80:
            bear_cross = True

    score_long = 0
    score_short = 0
    if is_oversold:  score_long  += 5
    if bull_cross:   score_long  += 8
    if is_overbought: score_short += 5
    if bear_cross:    score_short += 8

    return {
        'k':            k,
        'd':            d,
        'k_current':    k_cur,
        'd_current':    d_cur,
        'is_oversold':  is_oversold,
        'is_overbought': is_overbought,
        'bull_cross':   bull_cross,
        'bear_cross':   bear_cross,
        'score_long':   score_long,
        'score_short':  score_short,
    }


# ─── MACD ─────────────────────────────────────────────────────────────────────

def macd(closes: np.ndarray, fast: int = 12, slow: int = 26,
         signal: int = 9) -> dict:
    """
    MACD Line = EMA(fast) - EMA(slow)
    Signal    = EMA(MACD, signal_period)
    Histogram = MACD - Signal
    """
    closes = np.asarray(closes, dtype=float)

    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)

    macd_line = ema_fast - ema_slow
    macd_line[np.isnan(ema_fast) | np.isnan(ema_slow)] = np.nan

    signal_line = _ema(macd_line, signal)
    histogram   = macd_line - signal_line
    histogram[np.isnan(macd_line) | np.isnan(signal_line)] = np.nan

    def last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if len(valid) else np.nan

    macd_cur   = last_valid(macd_line)
    signal_cur = last_valid(signal_line)
    hist_cur   = last_valid(histogram)

    # Cross detection
    bull_cross = False
    bear_cross = False
    valid_both = ~(np.isnan(macd_line) | np.isnan(signal_line))
    valid_idx  = np.where(valid_both)[0]
    if len(valid_idx) >= 2:
        i_last = valid_idx[-1]
        i_prev = valid_idx[-2]
        prev_diff = macd_line[i_prev] - signal_line[i_prev]
        curr_diff = macd_line[i_last] - signal_line[i_last]
        if prev_diff <= 0 and curr_diff > 0:
            bull_cross = True
        if prev_diff >= 0 and curr_diff < 0:
            bear_cross = True

    above_zero = bool(not np.isnan(macd_cur) and macd_cur > 0)

    # Histogram increasing: last 2 valid histogram values
    hist_increasing = False
    valid_hist = histogram[~np.isnan(histogram)]
    if len(valid_hist) >= 2:
        hist_increasing = bool(valid_hist[-1] > valid_hist[-2])

    bull_div, bear_div = _detect_divergence(closes, macd_line, 20)

    score_long = 0
    score_short = 0
    if bull_cross:       score_long  += 8
    if above_zero:       score_long  += 4
    if hist_increasing:  score_long  += 3
    if bull_div:         score_long  += 6
    if bear_cross:       score_short += 8
    if not above_zero:   score_short += 4
    if not hist_increasing and not np.isnan(hist_cur): score_short += 3
    if bear_div:         score_short += 6

    return {
        'macd':               macd_line,
        'signal':             signal_line,
        'histogram':          histogram,
        'macd_current':       macd_cur,
        'signal_current':     signal_cur,
        'hist_current':       hist_cur,
        'bull_cross':         bull_cross,
        'bear_cross':         bear_cross,
        'above_zero':         above_zero,
        'hist_increasing':    hist_increasing,
        'bullish_divergence': bull_div,
        'bearish_divergence': bear_div,
        'score_long':         score_long,
        'score_short':        score_short,
    }


# ─── CCI (Commodity Channel Index) ───────────────────────────────────────────

def cci(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
        period: int = 20) -> dict:
    """
    Typical Price = (H + L + C) / 3
    CCI = (TP - SMA(TP, n)) / (0.015 * Mean Absolute Deviation)
    """
    highs  = np.asarray(highs,  dtype=float)
    lows   = np.asarray(lows,   dtype=float)
    closes = np.asarray(closes, dtype=float)
    n = len(closes)

    tp = (highs + lows + closes) / 3.0
    cci_arr = np.full(n, np.nan)

    for i in range(period - 1, n):
        window = tp[i - period + 1: i + 1]
        if np.any(np.isnan(window)):
            continue
        mean_tp = np.mean(window)
        mean_dev = np.mean(np.abs(window - mean_tp))
        if mean_dev == 0:
            cci_arr[i] = 0.0
        else:
            cci_arr[i] = (tp[i] - mean_tp) / (0.015 * mean_dev)

    def last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if len(valid) else np.nan

    current = last_valid(cci_arr)

    is_oversold  = bool(not np.isnan(current) and current < -100)
    is_overbought = bool(not np.isnan(current) and current > 100)

    # Crossed back: previously outside, now crossed the threshold
    crossed_oversold  = False
    crossed_overbought = False
    valid_cci = cci_arr[~np.isnan(cci_arr)]
    if len(valid_cci) >= 2:
        prev = valid_cci[-2]
        curr = valid_cci[-1]
        crossed_oversold   = bool(prev < -100 and curr >= -100)
        crossed_overbought = bool(prev > 100  and curr <= 100)

    score_long = 0
    score_short = 0
    if is_oversold:       score_long  += 5
    if crossed_oversold:  score_long  += 8
    if is_overbought:     score_short += 5
    if crossed_overbought: score_short += 8

    return {
        'cci':                cci_arr,
        'current':            current,
        'is_oversold':        is_oversold,
        'is_overbought':      is_overbought,
        'crossed_oversold':   crossed_oversold,
        'crossed_overbought': crossed_overbought,
        'score_long':         score_long,
        'score_short':        score_short,
    }


# ─── Williams %R ─────────────────────────────────────────────────────────────

def williams_r(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
               period: int = 14) -> dict:
    """
    %R = (Highest_High - Close) / (Highest_High - Lowest_Low) * -100
    Range: -100 to 0
    Oversold: < -80, Overbought: > -20
    """
    highs  = np.asarray(highs,  dtype=float)
    lows   = np.asarray(lows,   dtype=float)
    closes = np.asarray(closes, dtype=float)
    n = len(closes)

    wr = np.full(n, np.nan)
    for i in range(period - 1, n):
        hh = np.max(highs[i - period + 1: i + 1])
        ll = np.min(lows[i  - period + 1: i + 1])
        denom = hh - ll
        if denom == 0:
            wr[i] = -50.0  # midpoint when no range
        else:
            wr[i] = (hh - closes[i]) / denom * -100.0

    def last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if len(valid) else np.nan

    current = last_valid(wr)

    is_oversold  = bool(not np.isnan(current) and current < -80)
    is_overbought = bool(not np.isnan(current) and current > -20)

    score_long = 0
    score_short = 0
    if is_oversold:   score_long  += 6
    if is_overbought: score_short += 6

    return {
        'williams_r':    wr,
        'current':       current,
        'is_oversold':   is_oversold,
        'is_overbought': is_overbought,
        'score_long':    score_long,
        'score_short':   score_short,
    }


# ─── ROC (Rate of Change) ─────────────────────────────────────────────────────

def roc(closes: np.ndarray, period: int = 12) -> dict:
    """
    ROC = (Close - Close[n]) / Close[n] * 100
    Measures momentum as percentage change over `period` bars.
    """
    closes = np.asarray(closes, dtype=float)
    n = len(closes)

    roc_arr = np.full(n, np.nan)
    for i in range(period, n):
        prev = closes[i - period]
        if prev != 0 and not np.isnan(prev):
            roc_arr[i] = (closes[i] - prev) / prev * 100.0

    def last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if len(valid) else np.nan

    current = last_valid(roc_arr)

    crossed_zero_up   = False
    crossed_zero_down = False
    valid_roc = roc_arr[~np.isnan(roc_arr)]
    if len(valid_roc) >= 2:
        prev = valid_roc[-2]
        curr = valid_roc[-1]
        crossed_zero_up   = bool(prev <= 0 and curr > 0)
        crossed_zero_down = bool(prev >= 0 and curr < 0)

    score_long = 0
    score_short = 0
    if crossed_zero_up:   score_long  += 5
    if not np.isnan(current) and current > 0: score_long  += 3
    if crossed_zero_down: score_short += 5
    if not np.isnan(current) and current < 0: score_short += 3

    return {
        'roc':              roc_arr,
        'current':          current,
        'crossed_zero_up':  crossed_zero_up,
        'crossed_zero_down': crossed_zero_down,
        'score_long':       score_long,
        'score_short':      score_short,
    }


# ─── MFI (Money Flow Index) ──────────────────────────────────────────────────

def mfi(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
        volumes: np.ndarray, period: int = 14) -> dict:
    """
    Typical Price  = (H + L + C) / 3
    Raw Money Flow = TP * Volume
    Money Flow +   = sum of RMF where TP > TP[prev]
    Money Flow -   = sum of RMF where TP < TP[prev]
    MFR = MF+ / MF-
    MFI = 100 - 100 / (1 + MFR)
    """
    highs   = np.asarray(highs,   dtype=float)
    lows    = np.asarray(lows,    dtype=float)
    closes  = np.asarray(closes,  dtype=float)
    volumes = np.asarray(volumes, dtype=float)
    n = len(closes)

    tp  = (highs + lows + closes) / 3.0
    rmf = tp * volumes

    mfi_arr = np.full(n, np.nan)

    for i in range(period, n):
        pos_mf = 0.0
        neg_mf = 0.0
        for j in range(i - period + 1, i + 1):
            if j == 0:
                continue
            if tp[j] > tp[j - 1]:
                pos_mf += rmf[j]
            elif tp[j] < tp[j - 1]:
                neg_mf += rmf[j]
        if neg_mf == 0:
            mfi_arr[i] = 100.0
        else:
            mfr = pos_mf / neg_mf
            mfi_arr[i] = 100.0 - 100.0 / (1.0 + mfr)

    def last_valid(arr):
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if len(valid) else np.nan

    current = last_valid(mfi_arr)

    is_oversold  = bool(not np.isnan(current) and current < 20)
    is_overbought = bool(not np.isnan(current) and current > 80)

    score_long = 0
    score_short = 0
    if is_oversold:   score_long  += 7
    if is_overbought: score_short += 7

    return {
        'mfi':           mfi_arr,
        'current':       current,
        'is_oversold':   is_oversold,
        'is_overbought': is_overbought,
        'score_long':    score_long,
        'score_short':   score_short,
    }
