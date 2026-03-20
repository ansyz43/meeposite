"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-03-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), unique=True, index=True),
        sa.Column('google_id', sa.String(255), unique=True, index=True),
        sa.Column('auth_provider', sa.String(20)),
        sa.Column('ref_code', sa.String(16), unique=True, index=True),
        sa.Column('referred_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), index=True),
        sa.Column('cashback_balance', sa.Numeric(12, 2), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'bots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), unique=True, nullable=True),
        sa.Column('bot_token_encrypted', sa.String(500), nullable=False),
        sa.Column('bot_username', sa.String(255)),
        sa.Column('assistant_name', sa.String(255), nullable=False, server_default='Ассистент'),
        sa.Column('seller_link', sa.String(500)),
        sa.Column('greeting_message', sa.Text()),
        sa.Column('bot_description', sa.Text()),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('allow_partners', sa.Boolean(), server_default='false'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('bot_id', sa.Integer(), sa.ForeignKey('bots.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False, index=True),
        sa.Column('telegram_username', sa.String(255)),
        sa.Column('first_name', sa.String(255)),
        sa.Column('last_name', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('first_message_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_message_at', sa.DateTime()),
        sa.Column('message_count', sa.Integer(), server_default='0'),
        sa.Column('link_sent', sa.Boolean(), server_default='false'),
        sa.UniqueConstraint('bot_id', 'telegram_id'),
    )

    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('contact_id', sa.Integer(), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role', sa.String(10), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(255), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), server_default='false'),
    )

    op.create_table(
        'referral_partners',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('bot_id', sa.Integer(), sa.ForeignKey('bots.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('seller_link', sa.String(500), nullable=False),
        sa.Column('ref_code', sa.String(16), unique=True, nullable=False, index=True),
        sa.Column('credits', sa.Integer(), server_default='5'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'bot_id'),
    )

    op.create_table(
        'referral_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('partner_id', sa.Integer(), sa.ForeignKey('referral_partners.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('contact_id', sa.Integer(), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.UniqueConstraint('partner_id', 'telegram_id'),
    )

    op.create_table(
        'broadcasts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('bot_id', sa.Integer(), sa.ForeignKey('bots.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('image_url', sa.String(500)),
        sa.Column('total_contacts', sa.Integer(), server_default='0'),
        sa.Column('sent_count', sa.Integer(), server_default='0'),
        sa.Column('failed_count', sa.Integer(), server_default='0'),
        sa.Column('status', sa.String(20), server_default="'pending'"),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'cashback_transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('from_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('source_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('cashback_transactions')
    op.drop_table('broadcasts')
    op.drop_table('referral_sessions')
    op.drop_table('referral_partners')
    op.drop_table('password_reset_tokens')
    op.drop_table('messages')
    op.drop_table('contacts')
    op.drop_table('bots')
    op.drop_table('users')
