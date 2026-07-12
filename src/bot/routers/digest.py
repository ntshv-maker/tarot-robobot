from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import evening_spread_keyboard, funnel_day2_keyboard
from src.config import Settings
from src.db.models import ProductType
from src.db.repositories import UserRepository
from src.services.content_generation import ContentGenerationService
from src.utils.telegram_format import sanitize_telegram_html, send_thinking_sticker

router = Router()


@router.callback_query(F.data == "digest:enable")
async def digest_enable(callback: CallbackQuery, session: AsyncSession) -> None:
    users = UserRepository(session)
    user = await users.get_by_telegram_id(callback.from_user.id)
    if user:
        await users.update_profile(user, morning_digest_enabled=True)
    await callback.message.answer("📬 Отлично! Буду присылать карту дня каждое утро ✨")
    await callback.answer()


@router.callback_query(F.data == "digest:disable")
async def digest_disable(callback: CallbackQuery, session: AsyncSession) -> None:
    users = UserRepository(session)
    user = await users.get_by_telegram_id(callback.from_user.id)
    if user:
        await users.update_profile(user, morning_digest_enabled=False)
    await callback.message.answer("Хорошо, не буду беспокоить 🌙")
    await callback.answer()


@router.callback_query(F.data.startswith("funnel:"))
async def funnel_mini(callback: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    kind = callback.data.split(":")[1]
    mapping = {
        "love": ProductType.LOVE,
        "wealth": ProductType.WEALTH,
        "advice": ProductType.DAILY_MORNING,
    }
    product = mapping.get(kind, ProductType.DAILY_MORNING)
    users = UserRepository(session)
    user = await users.get_by_telegram_id(callback.from_user.id)
    await send_thinking_sticker(callback.message, callback.bot, settings)
    svc = ContentGenerationService(settings, session)
    text = await svc.generate(user, product, version="mini")
    await callback.message.answer(sanitize_telegram_html(text))
    await callback.answer()


@router.callback_query(F.data == "evening:spread")
async def evening_spread(callback: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    users = UserRepository(session)
    user = await users.get_by_telegram_id(callback.from_user.id)
    await send_thinking_sticker(callback.message, callback.bot, settings)
    svc = ContentGenerationService(settings, session)
    text = await svc.generate(user, ProductType.EVENING_SPREAD, version="full")
    await callback.message.answer(sanitize_telegram_html(text))
    await callback.answer()


@router.callback_query(F.data == "daily:another_advice")
async def another_advice(callback: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    users = UserRepository(session)
    user = await users.get_by_telegram_id(callback.from_user.id)
    svc = ContentGenerationService(settings, session)
    text = await svc.generate(user, ProductType.DAILY_MORNING, version="mini")
    await callback.message.answer(sanitize_telegram_html(text))
    await callback.answer()
