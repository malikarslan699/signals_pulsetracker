from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Delivery channel: telegram | email | webhook
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Filters
    min_confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    directions: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        server_default='{"LONG","SHORT"}',
    )
    timeframes: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        server_default='{"1H","4H"}',
    )
    markets: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        server_default='{"crypto"}',
    )
    # None = all pairs; otherwise restrict to this list
    pairs: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship("User", back_populates="alert_configs")

    def __repr__(self) -> str:
        return (
            f"<AlertConfig id={self.id} user_id={self.user_id} channel={self.channel}>"
        )
