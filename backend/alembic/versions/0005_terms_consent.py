"""Add terms acceptance fields to users and contacts.

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("terms_accepted_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("terms_version", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("terms_ip", sa.String(length=64), nullable=True))

    op.add_column("contacts", sa.Column("terms_accepted_at", sa.DateTime(), nullable=True))
    op.add_column("contacts", sa.Column("terms_version", sa.String(length=20), nullable=True))
    op.add_column("contacts", sa.Column("terms_source", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("contacts", "terms_source")
    op.drop_column("contacts", "terms_version")
    op.drop_column("contacts", "terms_accepted_at")
    op.drop_column("users", "terms_ip")
    op.drop_column("users", "terms_version")
    op.drop_column("users", "terms_accepted_at")
