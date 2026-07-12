from __future__ import annotations

from aiogram.methods import (
    AnswerCallbackQuery,
    EditMessageText,
    SendMessage,
    SendPhoto,
    SendSticker,
    TelegramMethod,
)
from aiogram.types import CallbackQuery, Message, Update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ChatDirection
from src.db.repositories import ChatMessageRepository


def _truncate(text: str | None, limit: int = 4000) -> str | None:
    if text is None:
        return None
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


async def log_incoming_update(session: AsyncSession, update: Update) -> None:
    repo = ChatMessageRepository(session)
    if update.message:
        await _log_incoming_message(repo, update.message)
    elif update.callback_query:
        await _log_incoming_callback(repo, update.callback_query)


async def _log_incoming_message(repo: ChatMessageRepository, message: Message) -> None:
    telegram_id = message.from_user.id if message.from_user else message.chat.id
    message_type = "text"
    text: str | None = message.text or message.caption

    if message.photo:
        message_type = "photo"
        if not text:
            text = "[фото]"
    elif message.sticker:
        message_type = "sticker"
        text = message.sticker.emoji or "[стикер]"
    elif message.document:
        message_type = "document"
        text = message.document.file_name or "[файл]"
    elif message.voice:
        message_type = "voice"
        text = "[голосовое]"
    elif message.text and message.text.startswith("/"):
        message_type = "command"

    await repo.log(
        telegram_id=telegram_id,
        direction=ChatDirection.IN,
        message_type=message_type,
        text=_truncate(text),
        telegram_message_id=message.message_id,
    )


async def _log_incoming_callback(repo: ChatMessageRepository, callback: CallbackQuery) -> None:
    if not callback.from_user:
        return
    label = callback.message.text if callback.message and callback.message.text else ""
    if len(label) > 120:
        label = label[:117] + "..."
    text = f"[кнопка] {callback.data}"
    if label:
        text = f"{text}\n↳ «{label}»"

    await repo.log(
        telegram_id=callback.from_user.id,
        direction=ChatDirection.IN,
        message_type="callback",
        text=_truncate(text),
        callback_data=callback.data,
        telegram_message_id=callback.message.message_id if callback.message else None,
    )


async def log_outgoing_method(session: AsyncSession, method: TelegramMethod) -> None:
    repo = ChatMessageRepository(session)
    telegram_id: int | None = None
    message_type = "text"
    text: str | None = None
    callback_data: str | None = None

    if isinstance(method, SendMessage):
        telegram_id = method.chat_id
        text = method.text
    elif isinstance(method, SendPhoto):
        telegram_id = method.chat_id
        message_type = "photo"
        text = method.caption or "[фото]"
    elif isinstance(method, SendSticker):
        telegram_id = method.chat_id
        message_type = "sticker"
        text = "[стикер]"
    elif isinstance(method, EditMessageText):
        telegram_id = method.chat_id
        message_type = "edit"
        text = method.text
    elif isinstance(method, AnswerCallbackQuery):
        message_type = "callback_answer"
        text = method.text or "[ответ на кнопку]"
        return
    else:
        return

    if telegram_id is None:
        return

    await repo.log(
        telegram_id=int(telegram_id),
        direction=ChatDirection.OUT,
        message_type=message_type,
        text=_truncate(text),
        callback_data=callback_data,
    )
