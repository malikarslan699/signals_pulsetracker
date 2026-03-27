from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Nested / embedded schemas
# ---------------------------------------------------------------------------

class ScoreBreakdown(BaseModel):
    """Per-indicator scores that make up the total confidence."""

    model_config = ConfigDict(extra="allow")

    trend_ema: Optional[int] = Field(default=None, ge=0, le=20)
    trend_macd: Optional[int] = Field(default=None, ge=0, le=20)
    trend_adx: Optional[int] = Field(default=None, ge=0, le=10)
    momentum_rsi: Optional[int] = Field(default=None, ge=0, le=15)
    momentum_stoch: Optional[int] = Field(default=None, ge=0, le=10)
    volume_obv: Optional[int] = Field(default=None, ge=0, le=10)
    volume_vwap: Optional[int] = Field(default=None, ge=0, le=10)
    volatility_bb: Optional[int] = Field(default=None, ge=0, le=5)
    ict_fvg: Optional[int] = Field(default=None, ge=0, le=10)
    ict_ob: Optional[int] = Field(default=None, ge=0, le=10)
    ict_liquidity: Optional[int] = Field(default=None, ge=0, le=10)
    support_resistance: Optional[int] = Field(default=None, ge=0, le=10)


class FVGZone(BaseModel):
    """Fair Value Gap zone."""

    high: Decimal
    low: Decimal
    direction: str  # BULLISH | BEARISH
    timestamp: int  # unix ms
    filled: bool = False


class OrderBlock(BaseModel):
    """ICT Order Block zone."""

    high: Decimal
    low: Decimal
    direction: str  # BULLISH | BEARISH
    strength: float  # 0.0 – 1.0
    timestamp: int


class LiquidityLevel(BaseModel):
    """Buy/sell-side liquidity pool."""

    price: Decimal
    side: str  # BSL | SSL  (buy-side | sell-side)
    swept: bool = False


class ICTZones(BaseModel):
    """All detected ICT market structure elements."""

    fvg_zones: List[FVGZone] = Field(default_factory=list)
    order_blocks: List[OrderBlock] = Field(default_factory=list)
    liquidity_levels: List[LiquidityLevel] = Field(default_factory=list)
    market_structure_break: Optional[str] = None  # BULLISH_BOS | BEARISH_BOS | CHoCH
    premium_discount: Optional[str] = None  # PREMIUM | DISCOUNT | EQ


class MTFScore(BaseModel):
    """Score for a single timeframe in multi-timeframe analysis."""

    timeframe: str
    direction: str  # LONG | SHORT | NEUTRAL
    score: int
    max_score: int


class MTFAnalysis(BaseModel):
    """Multi-timeframe confluence analysis."""

    scores: List[MTFScore] = Field(default_factory=list)
    overall_direction: str = "NEUTRAL"
    confluence_pct: float = 0.0  # % of timeframes agreeing with signal direction


# ---------------------------------------------------------------------------
# Signal CRUD schemas
# ---------------------------------------------------------------------------

class SignalCreate(BaseModel):
    """Internal schema — used by the analysis engine to persist a new signal."""

    pair_id: uuid.UUID
    symbol: str
    market: str
    direction: str = Field(pattern=r"^(LONG|SHORT)$")
    timeframe: str = Field(pattern=r"^(1m|3m|5m|15m|30m|1H|4H|1D|1W)$")
    confidence: int = Field(ge=0, le=100)
    entry: Decimal
    stop_loss: Decimal
    take_profit_1: Decimal
    take_profit_2: Optional[Decimal] = None
    take_profit_3: Optional[Decimal] = None
    rr_ratio: Optional[Decimal] = None
    raw_score: int
    max_possible_score: int
    score_breakdown: Optional[Dict[str, Any]] = None
    ict_zones: Optional[Dict[str, Any]] = None
    candle_snapshot: Optional[Dict[str, Any]] = None
    mtf_analysis: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class SignalResponse(BaseModel):
    """Full signal representation returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pair_id: uuid.UUID
    symbol: str
    market: str
    direction: str
    timeframe: str
    confidence: int
    entry: Decimal
    stop_loss: Decimal
    take_profit_1: Decimal
    take_profit_2: Optional[Decimal] = None
    take_profit_3: Optional[Decimal] = None
    rr_ratio: Optional[Decimal] = None
    raw_score: int
    max_possible_score: int
    status: str
    score_breakdown: Optional[Dict[str, Any]] = None
    ict_zones: Optional[Dict[str, Any]] = None
    candle_snapshot: Optional[Dict[str, Any]] = None
    mtf_analysis: Optional[Dict[str, Any]] = None
    fired_at: datetime
    expires_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    close_price: Optional[Decimal] = None
    pnl_pct: Optional[Decimal] = None
    alert_sent: bool


class SignalListResponse(BaseModel):
    """Paginated list of signals."""

    items: List[SignalResponse]
    total: int
    page: int
    limit: int
    pages: int


class SignalFilter(BaseModel):
    """Query parameters for filtering the signal list."""

    market: Optional[str] = None
    direction: Optional[str] = Field(default=None, pattern=r"^(LONG|SHORT)$")
    timeframe: Optional[str] = None
    min_confidence: Optional[int] = Field(default=None, ge=0, le=100)
    symbol: Optional[str] = None
    status: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"1m", "3m", "5m", "15m", "30m", "1H", "4H", "1D", "1W"}
        if v and v not in allowed:
            raise ValueError(f"timeframe must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        allowed = {
            "active", "tp1_hit", "tp2_hit", "tp3_hit", "sl_hit", "expired"
        }
        if v and v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class SignalStatusUpdate(BaseModel):
    """Payload for updating a signal's lifecycle status."""

    status: str = Field(
        pattern=r"^(active|tp1_hit|tp2_hit|tp3_hit|sl_hit|expired)$"
    )
    close_price: Optional[Decimal] = None
