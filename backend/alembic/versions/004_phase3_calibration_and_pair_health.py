"""phase 3 calibration and pair health

Revision ID: 004_phase3_calibration
Revises: 003_phase2_signal_lifecycle
Create Date: 2026-03-28
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "004_phase3_calibration"
down_revision = "003_phase2_signal_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("signals", sa.Column("setup_score", sa.Integer(), nullable=True))
    op.add_column("signals", sa.Column("pwin_tp1", sa.Numeric(5, 2), nullable=True))
    op.add_column("signals", sa.Column("pwin_tp2", sa.Numeric(5, 2), nullable=True))
    op.add_column("signals", sa.Column("ranking_score", sa.Numeric(6, 2), nullable=True))
    op.create_index("ix_signals_setup_score", "signals", ["setup_score"], unique=False)
    op.create_index("ix_signals_ranking_score", "signals", ["ranking_score"], unique=False)

    op.add_column("pairs", sa.Column("auto_disabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("pairs", sa.Column("manual_override", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("pairs", sa.Column("health_score", sa.Numeric(5, 2), nullable=True))
    op.add_column("pairs", sa.Column("health_status", sa.String(length=20), nullable=True))
    op.add_column("pairs", sa.Column("disable_reason", sa.Text(), nullable=True))
    op.add_column("pairs", sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("pairs", "last_health_check_at")
    op.drop_column("pairs", "disable_reason")
    op.drop_column("pairs", "health_status")
    op.drop_column("pairs", "health_score")
    op.drop_column("pairs", "manual_override")
    op.drop_column("pairs", "auto_disabled")

    op.drop_index("ix_signals_ranking_score", table_name="signals")
    op.drop_index("ix_signals_setup_score", table_name="signals")
    op.drop_column("signals", "ranking_score")
    op.drop_column("signals", "pwin_tp2")
    op.drop_column("signals", "pwin_tp1")
    op.drop_column("signals", "setup_score")
