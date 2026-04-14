"""Content plan tables.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True),
        sa.Column("niche", sa.String(255), nullable=False),
        sa.Column("platforms", sa.Text(), nullable=False, server_default="instagram,telegram"),
        sa.Column("tone", sa.String(100), nullable=False, server_default="friendly"),
        sa.Column("target_audience", sa.Text(), nullable=False, server_default=""),
        sa.Column("topics", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "competitor_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("content_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("channel_username", sa.String(255), nullable=False),
        sa.Column("channel_title", sa.String(255), nullable=True),
        sa.Column("last_parsed_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("profile_id", "platform", "channel_username", name="uq_comp_profile_chan"),
    )

    op.create_table(
        "competitor_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform", sa.String(20), nullable=False, index=True),
        sa.Column("channel_username", sa.String(255), nullable=False, index=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("views", sa.Integer(), nullable=True),
        sa.Column("reactions", sa.Integer(), nullable=True),
        sa.Column("posted_at", sa.DateTime(), nullable=True),
        sa.Column("parsed_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "content_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("period_days", sa.Integer(), server_default="7"),
        sa.Column("status", sa.String(20), server_default="generating"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "content_plan_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("content_plans.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("post_type", sa.String(50), nullable=False),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("hashtags", sa.Text(), nullable=True),
        sa.Column("best_time", sa.String(20), nullable=True),
        sa.Column("is_edited", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("content_plan_items")
    op.drop_table("content_plans")
    op.drop_table("competitor_posts")
    op.drop_table("competitor_sources")
    op.drop_table("content_profiles")
