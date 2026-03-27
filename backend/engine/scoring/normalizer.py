"""
Score Normalization — PulseSignal Pro

Converts raw indicator aggregate scores into a 0-100 confidence value
and maps that value to a human-readable confidence band.
"""
import math


def normalize_score(raw_score: int, max_possible: int) -> int:
    """
    Normalize raw score to 0-100 confidence using a sigmoid-like curve.

    The non-linear curve spreads scores more evenly across the range:
      ratio = 0.10  →  confidence ≈  7
      ratio = 0.20  →  confidence ≈ 18
      ratio = 0.30  →  confidence ≈ 31
      ratio = 0.40  →  confidence ≈ 50   (inflection point)
      ratio = 0.50  →  confidence ≈ 67
      ratio = 0.60  →  confidence ≈ 80
      ratio = 0.70  →  confidence ≈ 88
      ratio = 0.80  →  confidence ≈ 93
      ratio = 0.90  →  confidence ≈ 97

    Design intent:
      - Very few conditions (ratio < 0.25)  →  0-30  (weak / noise)
      - Moderate confluence (0.25-0.50)     →  30-67 (developing)
      - Strong confluence (0.50-0.75)       →  67-90 (high quality)
      - Near-perfect setup (> 0.75)         →  90-100 (ultra-high)
    """
    if max_possible <= 0 or raw_score <= 0:
        return 0

    ratio = min(raw_score / max_possible, 1.0)

    # Sigmoid centred at 0.4 with steepness 10
    # f(x) = 1 / (1 + e^(-10 * (x - 0.4)))
    curve = 1.0 / (1.0 + math.exp(-10.0 * (ratio - 0.4)))
    confidence = int(round(curve * 100))
    return max(0, min(100, confidence))


def score_to_confidence_band(confidence: int) -> str:
    """
    Map a 0-100 confidence value to a named quality band.

    Thresholds (inclusive):
      ULTRA_HIGH  ≥ 85
      HIGH        ≥ 70
      MEDIUM      ≥ 55
      LOW         ≥ 40
      NO_SIGNAL    < 40
    """
    if confidence >= 85:
        return 'ULTRA_HIGH'
    elif confidence >= 70:
        return 'HIGH'
    elif confidence >= 55:
        return 'MEDIUM'
    elif confidence >= 40:
        return 'LOW'
    else:
        return 'NO_SIGNAL'


# ---------------------------------------------------------------------------
# Metadata tables — used by UI and Telegram formatter
# ---------------------------------------------------------------------------

CONFIDENCE_BAND_DESCRIPTIONS: dict[str, str] = {
    'ULTRA_HIGH': 'Ultra High — All systems aligned, act with full confidence',
    'HIGH':       'High — Strong confluence, excellent setup',
    'MEDIUM':     'Medium — Good setup, wait for candle confirmation',
    'LOW':        'Low — Partial setup, reduce position size',
    'NO_SIGNAL':  'No Signal — Insufficient confluence, do not trade',
}

CONFIDENCE_BAND_COLORS: dict[str, str] = {
    'ULTRA_HIGH': '#10B981',  # emerald-500
    'HIGH':       '#34D399',  # emerald-400
    'MEDIUM':     '#F59E0B',  # amber-500
    'LOW':        '#EF4444',  # red-500
    'NO_SIGNAL':  '#6B7280',  # gray-500
}

CONFIDENCE_BAND_EMOJIS: dict[str, str] = {
    'ULTRA_HIGH': '⚡',
    'HIGH':       '✅',
    'MEDIUM':     '🔶',
    'LOW':        '⚠️',
    'NO_SIGNAL':  '❌',
}

CONFIDENCE_BAND_MIN_SCORES: dict[str, int] = {
    'ULTRA_HIGH': 85,
    'HIGH':       70,
    'MEDIUM':     55,
    'LOW':        40,
    'NO_SIGNAL':  0,
}
