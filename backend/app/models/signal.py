from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.services.signal_lifecycle import (
    LOSS_SIGNAL_STATUSES,
    OPEN_SIGNAL_STATUSES,
    WIN_SIGNAL_STATUSES,
)


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Reference to pair
    pair_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pairs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(20), nullable=False)

    # Signal direction and timeframe
    direction: Mapped[str] = mapped_column(String(5), nullable=False)  # LONG | SHORT
    timeframe: Mapped[str] = mapped_column(
        String(5), nullable=False
    )  # 5m | 15m | 1H | 4H | 1D

    # Confidence & scoring
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    setup_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    pwin_tp1: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    pwin_tp2: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    ranking_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True, index=True)
    raw_score: Mapped[int] = mapped_column(Integer, nullable=False)
    max_possible_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Price levels
    entry: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    entry_zone_low: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8), nullable=True
    )
    entry_zone_high: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8), nullable=True
    )
    entry_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    entry_trigger: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    invalidation_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8), nullable=True
    )
    take_profit_1: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    take_profit_2: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8), nullable=True
    )
    take_profit_3: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8), nullable=True
    )
    rr_ratio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    # Status lifecycle
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="CREATED"
    )  # CREATED | ARMED | FILLED | TP1_REACHED | TP2_REACHED | STOPPED | EXPIRED | INVALIDATED

    # JSON analytics fields
    score_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    setup_reasons: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    ict_zones: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    candle_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    mtf_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    fired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    filled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Close / PnL tracking
    fill_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    close_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    pnl_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    close_reason: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Alert tracking
    alert_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    pair = relationship("Pair", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<Signal id={self.id} symbol={self.symbol} "
            f"direction={self.direction} confidence={self.confidence}>"
        )

    @property
    def is_active(self) -> bool:
        return self.status in OPEN_SIGNAL_STATUSES

    @property
    def hit_tp(self) -> bool:
        return self.status in WIN_SIGNAL_STATUSES

    @property
    def hit_sl(self) -> bool:
        return self.status in LOSS_SIGNAL_STATUSES
