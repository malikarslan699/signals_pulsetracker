"""signal audit schema hardening

Revision ID: 005_signal_audit_schema
Revises: 004_phase3_calibration
Create Date: 2026-03-28
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "005_signal_audit_schema"
down_revision = "004_phase3_calibration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("signals", sa.Column("entry_trigger", sa.String(length=24), nullable=True))
    op.add_column("signals", sa.Column("setup_reasons", sa.JSON(), nullable=True))
    op.add_column("signals", sa.Column("model_version", sa.String(length=64), nullable=True))
    op.add_column(
        "signals",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.add_column(
        "signals",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.add_column("signals", sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("signals", sa.Column("fill_price", sa.Numeric(20, 8), nullable=True))
    op.add_column("signals", sa.Column("close_reason", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("signals", "close_reason")
    op.drop_column("signals", "fill_price")
    op.drop_column("signals", "filled_at")
    op.drop_column("signals", "updated_at")
    op.drop_column("signals", "created_at")
    op.drop_column("signals", "model_version")
    op.drop_column("signals", "setup_reasons")
    op.drop_column("signals", "entry_trigger")
