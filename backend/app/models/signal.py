from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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
    raw_score: Mapped[int] = mapped_column(Integer, nullable=False)
    max_possible_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Price levels
    entry: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
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
        String(20), nullable=False, default="active"
    )  # active | tp1_hit | tp2_hit | tp3_hit | sl_hit | expired

    # JSON analytics fields
    score_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ict_zones: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    candle_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    mtf_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    fired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Close / PnL tracking
    close_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    pnl_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

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
        return self.status == "active"

    @property
    def hit_tp(self) -> bool:
        return self.status in ("tp1_hit", "tp2_hit", "tp3_hit")

    @property
    def hit_sl(self) -> bool:
        return self.status == "sl_hit"
