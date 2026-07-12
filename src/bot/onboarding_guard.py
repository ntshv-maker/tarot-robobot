from __future__ import annotations

from aiogram.types import Message, ReplyKeyboardRemove

from src.db.models import User


async def ensure_onboarding_complete(message: Message, user: User | None) -> bool:
    if user and user.onboarding_complete:
        return True
    await message.answer(
        "Сначала пройди регистрацию — нажми /start и заполни анкету до конца.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return False
