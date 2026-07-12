from __future__ import annotations

import structlog
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.bot.keyboards import (
    another_advice_keyboard,
    digest_opt_in_keyboard,
    evening_spread_keyboard,
    funnel_day2_keyboard,
    subscription_plans_keyboard,
    product_inline_keyboard,
)
from src.config import Settings
from src.db.models import ProductType
from src.db.repositories import ReferralRepository, PurchaseRepository, UserRepository
from src.engines.tarot import daily_card
from src.services.content_generation import ContentGenerationService
from src.services.referral import ReferralService
from src.utils.tarot_image import render_daily_card_image
from src.utils.telegram_format import sanitize_telegram_html

logger = structlog.get_logger()


class SchedulerService:
    def __init__(
        self,
        bot: Bot,
        settings: Settings,
        session_factory: async_sessionmaker,
        redis: Redis,
    ) -> None:
        self.bot = bot
        self.settings = settings
        self.session_factory = session_factory
        self.redis = redis
        self.scheduler = AsyncIOScheduler(timezone=settings.tz)

    async def _dedupe(self, key: str) -> bool:
        ok = await self.redis.set(key, "1", nx=True, ex=86400)
        return bool(ok)

    async def morning_digest(self) -> None:
        async with self.session_factory() as session:
            users = UserRepository(session)
            for user in await users.list_for_morning_digest():
                key = f"digest:morning:{user.id}:{date_key()}"
                if not await self._dedupe(key):
                    continue
                try:
                    card = daily_card(user.id)
                    svc = ContentGenerationService(self.settings, session)
                    text = await svc.generate(user, ProductType.DAILY_MORNING, version="mini")
                    img_path = render_daily_card_image(
                        user.name or "Друг",
                        card.index,
                        date_key(),
                    )
                    from aiogram.types import FSInputFile

                    await self.bot.send_photo(
                        user.telegram_id,
                        FSInputFile(img_path),
                        caption=sanitize_telegram_html(text)[:1024],
                        reply_markup=another_advice_keyboard(),
                    )
                except Exception as exc:
                    logger.warning("morning_digest_failed", user_id=user.id, error=str(exc))

    async def weekly_horoscope(self) -> None:
        async with self.session_factory() as session:
            users = UserRepository(session)
            for user in await users.list_for_weekly_horoscope():
                key = f"digest:weekly:{user.id}:{date_key()}"
                if not await self._dedupe(key):
                    continue
                try:
                    svc = ContentGenerationService(self.settings, session)
                    text = await svc.generate(user, ProductType.WEEKLY_HOROSCOPE, version="full")
                    await self.bot.send_message(
                        user.telegram_id,
                        sanitize_telegram_html(text),
                        reply_markup=product_inline_keyboard(),
                    )
                except Exception as exc:
                    logger.warning("weekly_failed", user_id=user.id, error=str(exc))

    async def evening_reengagement(self) -> None:
        from datetime import datetime, timezone

        today = datetime.now(self.settings.tz).date()
        async with self.session_factory() as session:
            users = UserRepository(session)
            for user in await users.list_for_morning_digest():
                if user.last_active_at and user.last_active_at.astimezone(self.settings.tz).date() == today:
                    continue
                key = f"digest:evening:{user.id}:{date_key()}"
                if not await self._dedupe(key):
                    continue
                try:
                    await self.bot.send_message(
                        user.telegram_id,
                        f"🌙 Добрый вечер, {user.name or 'дорогая'}!\n\n"
                        "Как прошёл твой день? Если хочешь — сделаю вечерний расклад:",
                        reply_markup=evening_spread_keyboard(),
                    )
                except Exception as exc:
                    logger.warning("evening_failed", user_id=user.id, error=str(exc))

    async def funnel_day2(self) -> None:
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        async with self.session_factory() as session:
            users = UserRepository(session)
            for user in await users.list_inactive_funnel_day2(cutoff):
                key = f"funnel:day2:{user.id}"
                if not await self._dedupe(key):
                    continue
                try:
                    card = daily_card(user.id)
                    await self.bot.send_message(
                        user.telegram_id,
                        f"🃏 ВАША КАРТА ДНЯ: {card.name}\n\n"
                        "✨ Хотите получать карту каждое утро?",
                        reply_markup=digest_opt_in_keyboard(),
                    )
                    await self.bot.send_message(
                        user.telegram_id,
                        "👋 Привет! Что беспокоит?\nВыбери тему для бесплатного мини-расклада:",
                        reply_markup=funnel_day2_keyboard(),
                    )
                    await users.update_profile(user, funnel_day=2)
                except Exception as exc:
                    logger.warning("funnel_day2_failed", user_id=user.id, error=str(exc))

    async def referral_followup(self) -> None:
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(days=4)
        window_end = now - timedelta(days=3)
        async with self.session_factory() as session:
            purchases = PurchaseRepository(session)
            users = UserRepository(session)
            referral = ReferralService(self.settings, users, ReferralRepository(session))
            for purchase in await purchases.list_referral_followup(window_end, window_start):
                key = f"referral:followup:{purchase.id}"
                if not await self._dedupe(key):
                    continue
                user = await users.get_by_id(purchase.user_id)
                if not user:
                    continue
                try:
                    link = referral.referral_link(user)
                    await self.bot.send_message(
                        user.telegram_id,
                        "👥 ПРИВЕДИ ПОДРУГУ\n\n"
                        "Порекомендуй бота подруге и получи скидку 20% 🥰\n\n"
                        f"🔗 {link}",
                    )
                except Exception as exc:
                    logger.warning("referral_followup_failed", error=str(exc))

    async def no_purchase_nudge(self) -> None:
        async with self.session_factory() as session:
            users = UserRepository(session)
            purchases = PurchaseRepository(session)
            for user in await users.list_inactive_funnel_day2(
                __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            ):
                if user.funnel_day != 2:
                    continue
                if await purchases.user_has_any_purchase(user.id):
                    continue
                key = f"nudge:no_purchase:{user.id}"
                if not await self._dedupe(key):
                    continue
                try:
                    await self.bot.send_message(
                        user.telegram_id,
                        f"{user.name}, пока не выбрали тариф — может, персональная скидка поможет?\n\n"
                        "Вы можете вернуться в любой момент!",
                        reply_markup=subscription_plans_keyboard(ProductType.LOVE),
                    )
                except Exception as exc:
                    logger.warning("nudge_failed", error=str(exc))

    async def expire_subscriptions(self) -> None:
        from src.db.repositories import SubscriptionRepository

        async with self.session_factory() as session:
            count = await SubscriptionRepository(session).deactivate_expired()
            if count:
                logger.info("subscriptions_expired", count=count)

    def start(self) -> None:
        tz = self.settings.tz
        self.scheduler.add_job(
            self.morning_digest,
            CronTrigger(hour=self.settings.morning_digest_hour, minute=0, timezone=tz),
        )
        self.scheduler.add_job(
            self.weekly_horoscope,
            CronTrigger(day_of_week="mon", hour=self.settings.weekly_horoscope_hour, minute=0, timezone=tz),
        )
        self.scheduler.add_job(
            self.evening_reengagement,
            CronTrigger(hour=self.settings.evening_digest_hour, minute=0, timezone=tz),
        )
        self.scheduler.add_job(self.funnel_day2, CronTrigger(hour=10, minute=0, timezone=tz))
        self.scheduler.add_job(self.referral_followup, CronTrigger(hour=11, minute=0, timezone=tz))
        self.scheduler.add_job(self.no_purchase_nudge, CronTrigger(hour=12, minute=0, timezone=tz))
        self.scheduler.add_job(self.expire_subscriptions, CronTrigger(hour=0, minute=5, timezone=tz))
        self.scheduler.start()
        logger.info("scheduler_started")


def date_key() -> str:
    from datetime import datetime

    from src.config import get_settings

    return datetime.now(get_settings().tz).strftime("%Y-%m-%d")
