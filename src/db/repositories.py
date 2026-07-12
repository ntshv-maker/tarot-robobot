from __future__ import annotations

import secrets
import string
from datetime import date, datetime, time, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import (
    ChatDirection,
    ChatMessage,
    ContentVersion,
    GeneratedContent,
    ProductType,
    Purchase,
    PurchaseStatus,
    Referral,
    Subscription,
    User,
)


def generate_referral_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_referral_code(self, code: str) -> User | None:
        result = await self.session.execute(select(User).where(User.referral_code == code.upper()))
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.username = username
            user.first_name = first_name
            user.last_active_at = datetime.now(timezone.utc)
            await self.session.commit()
            return user

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            referral_code=generate_referral_code(),
            last_active_at=datetime.now(timezone.utc),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_profile(
        self,
        user: User,
        *,
        name: str | None = None,
        birth_date: date | None = None,
        birth_time: time | None = None,
        birth_place: str | None = None,
        partner_birth_date: date | None = None,
        zodiac_sign: str | None = None,
        life_path_number: int | None = None,
        consent_accepted_at: datetime | None = None,
        onboarding_step: str | None = None,
        morning_digest_enabled: bool | None = None,
        referred_by_user_id: int | None = None,
        funnel_day: int | None = None,
    ) -> User:
        if name is not None:
            user.name = name
        if birth_date is not None:
            user.birth_date = birth_date
        if birth_time is not None:
            user.birth_time = birth_time
        if birth_place is not None:
            user.birth_place = birth_place
        if partner_birth_date is not None:
            user.partner_birth_date = partner_birth_date
        if zodiac_sign is not None:
            user.zodiac_sign = zodiac_sign
        if life_path_number is not None:
            user.life_path_number = life_path_number
        if consent_accepted_at is not None:
            user.consent_accepted_at = consent_accepted_at
        if onboarding_step is not None:
            user.onboarding_step = onboarding_step
        if morning_digest_enabled is not None:
            user.morning_digest_enabled = morning_digest_enabled
        if referred_by_user_id is not None:
            user.referred_by_user_id = referred_by_user_id
        if funnel_day is not None:
            user.funnel_day = funnel_day
        user.last_active_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def list_for_morning_digest(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(
                User.morning_digest_enabled.is_(True),
                User.birth_date.is_not(None),
                User.consent_accepted_at.is_not(None),
            )
        )
        return list(result.scalars().all())

    async def list_for_weekly_horoscope(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.birth_date.is_not(None), User.consent_accepted_at.is_not(None))
        )
        return list(result.scalars().all())

    async def list_inactive_funnel_day2(self, cutoff: datetime) -> list[User]:
        result = await self.session.execute(
            select(User).where(
                User.funnel_day == 1,
                User.last_active_at.is_not(None),
                User.last_active_at < cutoff,
                User.birth_date.is_not(None),
            )
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.session.execute(select(User))
        return len(list(result.scalars().all()))

    async def list_for_dashboard(
        self,
        *,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[User]:
        query = select(User).order_by(User.last_active_at.desc().nullslast(), User.id.desc())
        if search:
            from sqlalchemy import or_

            term = f"%{search.strip()}%"
            filters = [
                User.name.ilike(term),
                User.username.ilike(term),
                User.first_name.ilike(term),
            ]
            if search.strip().isdigit():
                filters.append(User.telegram_id == int(search.strip()))
            query = query.where(or_(*filters))
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class PurchaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: int,
        product_type: ProductType,
        amount_rub: int,
        *,
        is_full_version: bool = True,
        partner_birth_date: date | None = None,
        question_text: str | None = None,
    ) -> Purchase:
        purchase = Purchase(
            user_id=user_id,
            product_type=product_type,
            amount_rub=amount_rub,
            is_full_version=is_full_version,
            partner_birth_date=partner_birth_date,
            question_text=question_text,
        )
        self.session.add(purchase)
        await self.session.commit()
        await self.session.refresh(purchase)
        return purchase

    async def get_by_id(self, purchase_id: int) -> Purchase | None:
        result = await self.session.execute(select(Purchase).where(Purchase.id == purchase_id))
        return result.scalar_one_or_none()

    async def mark_paid(self, purchase: Purchase) -> Purchase:
        purchase.status = PurchaseStatus.PAID
        purchase.paid_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(purchase)
        return purchase

    async def has_paid_product(self, user_id: int, product_type: ProductType) -> bool:
        result = await self.session.execute(
            select(Purchase).where(
                Purchase.user_id == user_id,
                Purchase.product_type == product_type,
                Purchase.status == PurchaseStatus.PAID,
            )
        )
        return result.scalar_one_or_none() is not None

    async def user_has_any_purchase(self, user_id: int) -> bool:
        result = await self.session.execute(
            select(Purchase).where(Purchase.user_id == user_id, Purchase.status == PurchaseStatus.PAID)
        )
        return result.scalar_one_or_none() is not None

    async def list_referral_followup(self, paid_before: datetime, paid_after: datetime) -> list[Purchase]:
        result = await self.session.execute(
            select(Purchase).where(
                Purchase.status == PurchaseStatus.PAID,
                Purchase.paid_at.is_not(None),
                Purchase.paid_at <= paid_before,
                Purchase.paid_at >= paid_after,
            )
        )
        return list(result.scalars().all())

    async def list_by_status(
        self,
        status: PurchaseStatus | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Purchase]:
        query = (
            select(Purchase)
            .options(selectinload(Purchase.user))
            .order_by(Purchase.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            query = query.where(Purchase.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self, status: PurchaseStatus | None = None) -> int:
        query = select(Purchase)
        if status is not None:
            query = query.where(Purchase.status == status)
        result = await self.session.execute(query)
        return len(list(result.scalars().all()))

    async def mark_cancelled(self, purchase: Purchase) -> Purchase:
        purchase.status = PurchaseStatus.CANCELLED
        await self.session.commit()
        await self.session.refresh(purchase)
        return purchase


class SubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: int,
        product_type: ProductType,
        starts_at: datetime,
        expires_at: datetime,
    ) -> Subscription:
        sub = Subscription(
            user_id=user_id,
            product_type=product_type,
            starts_at=starts_at,
            expires_at=expires_at,
            is_active=True,
        )
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)
        return sub

    async def get_active(self, user_id: int) -> list[Subscription]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active.is_(True),
                Subscription.expires_at > now,
            )
        )
        return list(result.scalars().all())

    async def deactivate_expired(self) -> int:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            update(Subscription)
            .where(Subscription.is_active.is_(True), Subscription.expires_at <= now)
            .values(is_active=False)
        )
        await self.session.commit()
        return result.rowcount or 0


class ContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(
        self,
        user_id: int,
        content_type: ProductType,
        version: str,
        text: str,
        input_payload: dict,
        telegram_message_id: int | None = None,
    ) -> GeneratedContent:
        content = GeneratedContent(
            user_id=user_id,
            content_type=content_type,
            version=ContentVersion(version),
            text=text,
            input_payload=input_payload,
            telegram_message_id=telegram_message_id,
        )
        self.session.add(content)
        await self.session.commit()
        await self.session.refresh(content)
        return content

    async def get_recent(
        self,
        user_id: int,
        content_type: ProductType,
        version: str,
        within_hours: int = 24,
    ) -> GeneratedContent | None:
        cutoff = datetime.now(timezone.utc).replace(microsecond=0)
        from datetime import timedelta

        cutoff = cutoff - timedelta(hours=within_hours)
        result = await self.session.execute(
            select(GeneratedContent)
            .where(
                GeneratedContent.user_id == user_id,
                GeneratedContent.content_type == content_type,
                GeneratedContent.version == ContentVersion(version),
                GeneratedContent.created_at >= cutoff,
            )
            .order_by(GeneratedContent.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, content_id: int) -> GeneratedContent | None:
        result = await self.session.execute(select(GeneratedContent).where(GeneratedContent.id == content_id))
        return result.scalar_one_or_none()


class ChatMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        *,
        telegram_id: int,
        direction: ChatDirection,
        message_type: str = "text",
        text: str | None = None,
        callback_data: str | None = None,
        telegram_message_id: int | None = None,
        user_id: int | None = None,
    ) -> ChatMessage:
        if user_id is None:
            user = await UserRepository(self.session).get_by_telegram_id(telegram_id)
            user_id = user.id if user else None

        msg = ChatMessage(
            user_id=user_id,
            telegram_id=telegram_id,
            direction=direction,
            message_type=message_type,
            text=text,
            callback_data=callback_data,
            telegram_message_id=telegram_message_id,
        )
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def list_for_user(
        self,
        user_id: int,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> list[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_for_user(self, user_id: int) -> int:
        result = await self.session.execute(select(ChatMessage).where(ChatMessage.user_id == user_id))
        return len(list(result.scalars().all()))


class ReferralRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, referrer_id: int, referred_id: int) -> Referral:
        referral = Referral(referrer_id=referrer_id, referred_id=referred_id)
        self.session.add(referral)
        await self.session.commit()
        await self.session.refresh(referral)
        return referral

    async def activate_reward(self, referrer_id: int, referred_id: int) -> None:
        result = await self.session.execute(
            select(Referral).where(
                Referral.referrer_id == referrer_id,
                Referral.referred_id == referred_id,
            )
        )
        referral = result.scalar_one_or_none()
        if referral and not referral.reward_applied:
            referral.activated_at = datetime.now(timezone.utc)
            referral.reward_applied = True
            referrer = await self.session.get(User, referrer_id)
            if referrer:
                referrer.referral_discount_percent = 20
            await self.session.commit()
