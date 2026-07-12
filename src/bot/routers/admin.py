from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.db.models import LlmUsageLog
from src.db.repositories import UserRepository
from src.services.payment_fulfillment import confirm_purchase

router = Router()


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_id_list


@router.message(Command("confirm_payment"))
async def confirm_payment(message: Message, session: AsyncSession, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Usage: /confirm_payment <id>")
        return
    purchase_id = int(parts[1])
    result = await confirm_purchase(message.bot, settings, session, purchase_id)
    await message.answer(f"{'✅' if result.status == 'ok' else '⚠️'} {result.message}")


@router.message(Command("llm_cost"))
async def llm_cost(message: Message, session: AsyncSession, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    total_row = await session.execute(
        select(
            func.coalesce(func.sum(LlmUsageLog.total_tokens), 0),
            func.coalesce(func.sum(LlmUsageLog.cost_rub), 0),
            func.count(LlmUsageLog.id),
        ).where(LlmUsageLog.success.is_(True))
    )
    total_tokens, total_rub, requests = total_row.one()

    today_row = await session.execute(
        select(
            func.coalesce(func.sum(LlmUsageLog.total_tokens), 0),
            func.coalesce(func.sum(LlmUsageLog.cost_rub), 0),
        ).where(LlmUsageLog.success.is_(True), func.date(LlmUsageLog.created_at) == func.current_date())
    )
    today_tokens, today_rub = today_row.one()

    await message.answer(
        "📊 Расход LLM (Gemini 2.5 Pro)\n\n"
        f"Всего запросов: {requests}\n"
        f"Всего токенов: {int(total_tokens)}\n"
        f"Всего: {float(total_rub):.4f} ₽\n\n"
        f"Сегодня токенов: {int(today_tokens)}\n"
        f"Сегодня: {float(today_rub):.4f} ₽\n\n"
        f"Курс USD→RUB: {settings.usd_to_rub_rate}\n"
        f"Input: ${settings.llm_input_usd_per_1m}/1M | Output: ${settings.llm_output_usd_per_1m}/1M"
    )


@router.message(Command("stats"))
async def stats(message: Message, session: AsyncSession, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    count = await UserRepository(session).count_all()
    await message.answer(f"👥 Пользователей: {count}")
