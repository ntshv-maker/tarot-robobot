from __future__ import annotations

from typing import Any, Callable, TypeVar

from aiogram import Bot
from aiogram.methods.base import TelegramMethod

from src.services.chat_log import log_outgoing_method

T = TypeVar("T")


class LoggingBot(Bot):
    def __init__(
        self,
        *args: Any,
        session_factory: Callable[[], Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._session_factory = session_factory

    async def __call__(self, method: TelegramMethod[T], request_timeout: int | None = None) -> T:
        result = await super().__call__(method, request_timeout=request_timeout)
        if self._session_factory:
            try:
                async with self._session_factory() as session:
                    await log_outgoing_method(session, method)
            except Exception:
                pass
        return result
