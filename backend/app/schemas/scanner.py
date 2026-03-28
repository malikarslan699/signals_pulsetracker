from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ScannerStatus(BaseModel):
    """Real-time status of the background scanner."""

    is_running: bool
    current_market: Optional[str] = None
    pairs_total: int = 0
    pairs_done: int = 0
    signals_found_this_run: int = 0
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    queue_length: int = 0
    uptime_seconds: Optional[float] = None


class ScannerRunResponse(BaseModel):
    """Persisted scanner run record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    market: str
    pairs_scanned: int
    signals_found: int
    duration_ms: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    error_message: Optional[str] = None


class PairResponse(BaseModel):
    """Trading pair information."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    market: str
    exchange: str
    base_asset: str
    quote_asset: str
    is_active: bool
    auto_disabled: bool = False
    manual_override: bool = False
    health_score: Optional[Decimal] = None
    health_status: Optional[str] = None
    disable_reason: Optional[str] = None
    last_health_check_at: Optional[datetime] = None
    precision_price: int
    precision_qty: int
    min_qty: Decimal
    created_at: datetime


class CandleResponse(BaseModel):
    """OHLCV candle data returned via REST."""

    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: int  # unix milliseconds


class IndicatorValues(BaseModel):
    """Snapshot of all computed indicator values for a symbol."""

    # Trend
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    adx: Optional[float] = None
    plus_di: Optional[float] = None
    minus_di: Optional[float] = None

    # Momentum
    rsi_14: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    cci: Optional[float] = None
    williams_r: Optional[float] = None

    # Volatility
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None
    atr_14: Optional[float] = None

    # Volume
    obv: Optional[float] = None
    vwap: Optional[float] = None
    volume_sma_20: Optional[float] = None
    volume_ratio: Optional[float] = None  # current / sma_20


class AnalysisResponse(BaseModel):
    """Full indicator analysis result for a trading pair."""

    symbol: str
    timeframe: str
    market: str
    timestamp: datetime
    price: float
    indicators: IndicatorValues
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    ict_zones: Dict[str, Any] = Field(default_factory=dict)
    mtf_analysis: Dict[str, Any] = Field(default_factory=dict)
    overall_direction: str = "NEUTRAL"  # LONG | SHORT | NEUTRAL
    confidence: int = Field(ge=0, le=100)
    signal_triggered: bool = False
    signal_id: Optional[uuid.UUID] = None
