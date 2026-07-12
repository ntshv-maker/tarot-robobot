from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import packages_keyboard
from src.db.repositories import UserRepository

router = Router()


@router.callback_query(F.data == "packages:show")
async def show_packages(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if not user or not user.onboarding_complete:
        await callback.message.answer("Сначала пройди регистрацию — нажми /start и заполни анкету.")
        await callback.answer()
        return

    await callback.message.answer(
        "📦 КОМБО-ПАКЕТЫ (Выгоднее, чем по отдельности)\n\n"
        "🎁 «Счастливая женщина» — 990₽\n"
        "💗 «ЛЮБОВЬ+» — 1200₽/мес\n"
        "👑 «VIP-пакет» — 2300₽/мес",
        reply_markup=packages_keyboard(),
    )
    await callback.answer()
