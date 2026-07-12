from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message


async def answer_callback(callback: CallbackQuery, text: str | None = None) -> None:
    try:
        await callback.answer(text)
    except TelegramBadRequest:
        pass


async def reply_to_callback(callback: CallbackQuery, text: str, **kwargs) -> Message | None:
    if callback.message:
        return await callback.message.answer(text, **kwargs)
    if callback.from_user:
        return await callback.bot.send_message(callback.from_user.id, text, **kwargs)
    return None
