from __future__ import annotations

import enum
from datetime import date, datetime, time
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProductType(str, enum.Enum):
    LOVE = "love"
    FORECAST_MONTH = "forecast_month"
    WEALTH = "wealth"
    NEGATIVE = "negative"
    QUESTION = "question"
    HAPPY_WOMAN = "happy_woman"
    LOVE_PLUS = "love_plus"
    VIP = "vip"
    NUMEROLOGY_PORTRAIT = "numerology_portrait"
    DAILY_MORNING = "daily_morning"
    WEEKLY_HOROSCOPE = "weekly_horoscope"
    EVENING_SPREAD = "evening_spread"
    FOLLOWUP = "followup"


class PurchaseStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class ChatDirection(str, enum.Enum):
    IN = "in"
    OUT = "out"


class ContentVersion(str, enum.Enum):
    MINI = "mini"
    FULL = "full"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    birth_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    birth_place: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    zodiac_sign: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    life_path_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    consent_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    onboarding_step: Mapped[str] = mapped_column(String(64), default="start")
    funnel_day: Mapped[int] = mapped_column(Integer, default=1)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    morning_digest_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    referral_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    referred_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    referral_discount_percent: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    referred_by: Mapped["Optional[User]"] = relationship("User", remote_side=[id])
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
    purchases: Mapped[list["Purchase"]] = relationship(back_populates="user")
    generated_contents: Mapped[list["GeneratedContent"]] = relationship(back_populates="user")

    @property
    def onboarding_complete(self) -> bool:
        return (
            self.birth_date is not None
            and self.name is not None
            and self.birth_place is not None
            and self.consent_accepted_at is not None
        )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_type: Mapped[ProductType] = mapped_column(Enum(ProductType))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)

    user: Mapped[User] = relationship(back_populates="subscriptions")


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_type: Mapped[ProductType] = mapped_column(Enum(ProductType))
    amount_rub: Mapped[int] = mapped_column(Integer)
    status: Mapped[PurchaseStatus] = mapped_column(Enum(PurchaseStatus), default=PurchaseStatus.PENDING)
    is_full_version: Mapped[bool] = mapped_column(Boolean, default=True)
    partner_birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    question_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_content_id: Mapped[Optional[int]] = mapped_column(ForeignKey("generated_contents.id"), nullable=True)
    payment_provider: Mapped[str] = mapped_column(String(32), default="manual")
    external_payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="purchases")


class GeneratedContent(Base):
    __tablename__ = "generated_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content_type: Mapped[ProductType] = mapped_column(Enum(ProductType))
    version: Mapped[ContentVersion] = mapped_column(Enum(ContentVersion))
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    text: Mapped[str] = mapped_column(Text)
    telegram_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="generated_contents")


class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message_type: Mapped[str] = mapped_column(String(64))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (UniqueConstraint("referrer_id", "referred_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    referred_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reward_applied: Mapped[bool] = mapped_column(Boolean, default=False)


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    __table_args__ = (UniqueConstraint("product_type", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_type: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(16))
    system_prompt: Mapped[str] = mapped_column(Text)
    user_prompt_template: Mapped[str] = mapped_column(Text)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    direction: Mapped[ChatDirection] = mapped_column(Enum(ChatDirection))
    message_type: Mapped[str] = mapped_column(String(32), default="text")
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    callback_data: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    telegram_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped[Optional[User]] = relationship()


class LlmUsageLog(Base):
    __tablename__ = "llm_usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    product_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model: Mapped[str] = mapped_column(String(128))
    request_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    input_cost_rub: Mapped[float] = mapped_column(Float, default=0.0)
    output_cost_rub: Mapped[float] = mapped_column(Float, default=0.0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    cost_rub: Mapped[float] = mapped_column(Float, default=0.0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
