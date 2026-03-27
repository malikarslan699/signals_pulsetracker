from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Pair(Base):
    __tablename__ = "pairs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )  # e.g. BTCUSDT
    market: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # crypto | forex
    exchange: Mapped[str] = mapped_column(
        String(30), nullable=False, default="binance"
    )
    base_asset: Mapped[str] = mapped_column(String(20), nullable=False)  # BTC
    quote_asset: Mapped[str] = mapped_column(String(20), nullable=False)  # USDT

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    precision_price: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    precision_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    min_qty: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0.001")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Pair symbol={self.symbol} market={self.market}>"
