"""
PulseSignal Pro — Indicator Engine
===================================
Clean public API for all technical indicators.

Usage example:
    from backend.engine.indicators import ema, rsi, supertrend, bollinger_bands
    from backend.engine.indicators import detect_market_structure, find_fib_retracement_zone
"""

# ── Trend ─────────────────────────────────────────────────────────────────────
from .trend import (
    ema,
    ema_stack,
    sma,
    sma_cross,
    wma,
    hma,
    hma_direction,
    dema,
    tema,
    supertrend,
    ichimoku,
)

# ── Momentum ──────────────────────────────────────────────────────────────────
from .momentum import (
    rsi,
    rsi_analysis,
    stochastic_rsi,
    macd,
    cci,
    williams_r,
    roc,
    mfi,
)

# ── Volatility ────────────────────────────────────────────────────────────────
from .volatility import (
    atr,
    atr_analysis,
    bollinger_bands,
    keltner_channels,
    donchian_channels,
)

# ── Volume ────────────────────────────────────────────────────────────────────
from .volume import (
    volume_spike,
    obv,
    vwap,
    cmf,
    vroc,
)

# ── Market Structure ──────────────────────────────────────────────────────────
from .structure import (
    SwingPoint,
    StructureLevel,
    find_swing_points,
    detect_market_structure,
    detect_support_resistance,
)

# ── Fibonacci ─────────────────────────────────────────────────────────────────
from .fibonacci import (
    FIBO_RETRACEMENT_LEVELS,
    FIBO_EXTENSION_LEVELS,
    fibonacci_retracement,
    find_fib_retracement_zone,
    calculate_tp_targets_fib,
)

__all__ = [
    # Trend
    "ema", "ema_stack",
    "sma", "sma_cross",
    "wma",
    "hma", "hma_direction",
    "dema", "tema",
    "supertrend",
    "ichimoku",

    # Momentum
    "rsi", "rsi_analysis",
    "stochastic_rsi",
    "macd",
    "cci",
    "williams_r",
    "roc",
    "mfi",

    # Volatility
    "atr", "atr_analysis",
    "bollinger_bands",
    "keltner_channels",
    "donchian_channels",

    # Volume
    "volume_spike",
    "obv",
    "vwap",
    "cmf",
    "vroc",

    # Market Structure
    "SwingPoint",
    "StructureLevel",
    "find_swing_points",
    "detect_market_structure",
    "detect_support_resistance",

    # Fibonacci
    "FIBO_RETRACEMENT_LEVELS",
    "FIBO_EXTENSION_LEVELS",
    "fibonacci_retracement",
    "find_fib_retracement_zone",
    "calculate_tp_targets_fib",
]
