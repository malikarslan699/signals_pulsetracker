"""phase 2 signal lifecycle fields

Revision ID: 003_phase2_signal_lifecycle
Revises: 002
Create Date: 2026-03-28
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "003_phase2_signal_lifecycle"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("signals", sa.Column("entry_zone_low", sa.Numeric(20, 8), nullable=True))
    op.add_column("signals", sa.Column("entry_zone_high", sa.Numeric(20, 8), nullable=True))
    op.add_column("signals", sa.Column("entry_type", sa.String(length=32), nullable=True))
    op.add_column("signals", sa.Column("invalidation_price", sa.Numeric(20, 8), nullable=True))
    op.add_column("signals", sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("signals", "valid_until")
    op.drop_column("signals", "invalidation_price")
    op.drop_column("signals", "entry_type")
    op.drop_column("signals", "entry_zone_high")
    op.drop_column("signals", "entry_zone_low")
