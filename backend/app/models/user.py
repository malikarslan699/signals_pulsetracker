from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.alert import AlertConfig
    from app.models.signal import Signal
    from app.models.subscription import Subscription


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Role: user | premium | admin | owner | reseller
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")

    # Plan: trial | monthly | yearly | lifetime
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="trial")
    plan_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Market access: crypto | forex | both
    market_access: Mapped[str] = mapped_column(String(10), nullable=False, default="both")

    # Telegram
    telegram_chat_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )
    telegram_username: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Anti-abuse / session
    device_fingerprint: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # Reseller hierarchy — FK to self
    reseller_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # API access
    api_key: Mapped[Optional[str]] = mapped_column(
        String(64), unique=True, nullable=True, index=True
    )

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

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    alert_configs: Mapped[List["AlertConfig"]] = relationship(
        "AlertConfig",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # Sub-users (reseller → resold users)
    resold_users: Mapped[List["User"]] = relationship(
        "User",
        foreign_keys=[reseller_id],
        back_populates="reseller",
        lazy="selectin",
    )
    reseller: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reseller_id],
        back_populates="resold_users",
        remote_side=[id],
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} plan={self.plan}>"

    @property
    def is_premium(self) -> bool:
        return self.plan in ("monthly", "yearly", "lifetime", "trial")

    @property
    def is_admin(self) -> bool:
        return self.role in ("admin", "owner", "superadmin")

    @property
    def is_owner(self) -> bool:
        return self.role == "owner"

    @property
    def is_reseller(self) -> bool:
        return self.role == "reseller"
