from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import subscription_plans_keyboard
from src.db.models import ProductType
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
        "✨ Подписка на полные разборы по всем темам:\n\n"
        "Выбери срок — после оплаты нажми «🔓 Полный разбор» под любым мини-разбором:",
        reply_markup=subscription_plans_keyboard(ProductType.LOVE),
    )
    await callback.answer()
