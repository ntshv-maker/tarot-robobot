from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.chat_log import log_incoming_update


class ChatLogMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session: AsyncSession | None = data.get("session")
        update = event if isinstance(event, Update) else data.get("event_update")
        if session and isinstance(update, Update):
            try:
                await log_incoming_update(session, update)
            except Exception:
                pass
        return await handler(event, data)
