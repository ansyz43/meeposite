"""Narrative core for content profiles + hunt stage / meepo CTA on plan items.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-22

Additive migration — all new columns are nullable / have safe defaults.
Does not touch existing columns or indexes, so it cannot break current features.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── content_profiles: narrative core + cached strategy ──
    op.add_column("content_profiles", sa.Column("founder_story", sa.Text(), nullable=True))
    op.add_column("content_profiles", sa.Column("transformation", sa.Text(), nullable=True))
    op.add_column("content_profiles", sa.Column("signature_metaphors", sa.Text(), nullable=True))
    op.add_column("content_profiles", sa.Column("value_ladder_position", sa.String(length=50), nullable=True))
    op.add_column("content_profiles", sa.Column("meepo_bot_deeplink", sa.String(length=500), nullable=True))
    op.add_column("content_profiles", sa.Column("strategy_json", sa.Text(), nullable=True))
    op.add_column("content_profiles", sa.Column("strategy_generated_at", sa.DateTime(), nullable=True))

    # ── content_plan_items: hunt stage + meepo CTA marker ──
    op.add_column("content_plan_items", sa.Column("hunt_stage", sa.String(length=20), nullable=True))
    op.add_column(
        "content_plan_items",
        sa.Column("is_meepo_cta", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("content_plan_items", "is_meepo_cta")
    op.drop_column("content_plan_items", "hunt_stage")
    op.drop_column("content_profiles", "strategy_generated_at")
    op.drop_column("content_profiles", "strategy_json")
    op.drop_column("content_profiles", "meepo_bot_deeplink")
    op.drop_column("content_profiles", "value_ladder_position")
    op.drop_column("content_profiles", "signature_metaphors")
    op.drop_column("content_profiles", "transformation")
    op.drop_column("content_profiles", "founder_story")
