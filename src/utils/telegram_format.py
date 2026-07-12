from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import Message

    from src.config import Settings


async def send_thinking_sticker(message: Message, bot: Bot, settings: Settings) -> None:
    if settings.typing_sticker_id:
        try:
            await bot.send_sticker(chat_id=message.chat.id, sticker=settings.typing_sticker_id)
        except Exception:
            pass


def sanitize_telegram_html(text: str) -> str:
    text = text.replace("**", "")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text[:4096]
