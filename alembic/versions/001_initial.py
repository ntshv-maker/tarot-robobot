"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255)),
        sa.Column("first_name", sa.String(255)),
        sa.Column("name", sa.String(255)),
        sa.Column("birth_date", sa.Date()),
        sa.Column("birth_time", sa.Time()),
        sa.Column("birth_place", sa.String(255)),
        sa.Column("zodiac_sign", sa.String(32)),
        sa.Column("life_path_number", sa.Integer()),
        sa.Column("consent_accepted_at", sa.DateTime(timezone=True)),
        sa.Column("onboarding_step", sa.String(64), server_default="start"),
        sa.Column("funnel_day", sa.Integer(), server_default="1"),
        sa.Column("last_active_at", sa.DateTime(timezone=True)),
        sa.Column("morning_digest_enabled", sa.Boolean(), server_default="false"),
        sa.Column("referral_code", sa.String(16), nullable=False),
        sa.Column("referred_by_user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("referral_discount_percent", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("telegram_id"),
        sa.UniqueConstraint("referral_code"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "generated_contents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "content_type",
            sa.Enum(
                "love", "forecast_month", "wealth", "negative", "question",
                "happy_woman", "love_plus", "vip", "numerology_portrait",
                "daily_morning", "weekly_horoscope", "evening_spread", "followup",
                name="producttype",
            ),
            nullable=False,
        ),
        sa.Column("version", sa.Enum("mini", "full", name="contentversion"), nullable=False),
        sa.Column("input_payload", postgresql.JSONB(), server_default="{}"),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("telegram_message_id", sa.BigInteger()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_type", sa.Enum(name="producttype", create_type=False), nullable=False),
        sa.Column("amount_rub", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "paid", "cancelled", name="purchasestatus"),
            server_default="pending",
        ),
        sa.Column("is_full_version", sa.Boolean(), server_default="true"),
        sa.Column("partner_birth_date", sa.Date()),
        sa.Column("question_text", sa.Text()),
        sa.Column("generated_content_id", sa.Integer(), sa.ForeignKey("generated_contents.id")),
        sa.Column("payment_provider", sa.String(32), server_default="manual"),
        sa.Column("external_payment_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_type", sa.Enum(name="producttype", create_type=False), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
    )

    op.create_table(
        "scheduled_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("message_type", sa.String(64), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("payload", postgresql.JSONB(), server_default="{}"),
    )

    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("referrer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("referred_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.Column("reward_applied", sa.Boolean(), server_default="false"),
        sa.UniqueConstraint("referrer_id", "referred_id"),
    )

    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_type", sa.String(64), nullable=False),
        sa.Column("version", sa.String(16), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("user_prompt_template", sa.Text(), nullable=False),
        sa.UniqueConstraint("product_type", "version"),
    )


def downgrade() -> None:
    op.drop_table("prompt_templates")
    op.drop_table("referrals")
    op.drop_table("scheduled_messages")
    op.drop_table("subscriptions")
    op.drop_table("purchases")
    op.drop_table("generated_contents")
    op.drop_table("users")
    sa.Enum(name="purchasestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="contentversion").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="producttype").drop(op.get_bind(), checkfirst=True)
