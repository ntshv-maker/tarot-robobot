from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import after_full_keyboard
from src.config import Settings
from src.constants import PRODUCT_LABELS
from src.db.models import ProductType, Purchase, PurchaseStatus
from src.db.repositories import ContentRepository, UserRepository
from src.services.content_generation import ContentGenerationService
from src.services.products import ProductService
from src.utils.telegram_format import sanitize_telegram_html


@dataclass
class FulfillmentResult:
    purchase_id: int
    status: str
    message: str
    user_telegram_id: int | None = None


async def confirm_purchase(
    bot: Bot,
    settings: Settings,
    session: AsyncSession,
    purchase_id: int,
) -> FulfillmentResult:
    product_svc = ProductService(session)
    purchase = await product_svc.purchases.get_by_id(purchase_id)
    if not purchase:
        return FulfillmentResult(purchase_id, "error", "Заказ не найден")
    if purchase.status == PurchaseStatus.PAID:
        return FulfillmentResult(purchase_id, "already_paid", "Оплата уже подтверждена")
    if purchase.status == PurchaseStatus.CANCELLED:
        return FulfillmentResult(purchase_id, "cancelled", "Заказ отменён")

    await product_svc.fulfill_purchase(purchase)
    user = await UserRepository(session).get_by_id(purchase.user_id)
    if not user:
        return FulfillmentResult(purchase_id, "error", "Пользователь не найден")

    product_label = PRODUCT_LABELS.get(purchase.product_type, purchase.product_type.value)

    if purchase.product_type in {ProductType.HAPPY_WOMAN, ProductType.LOVE_PLUS, ProductType.VIP}:
        await bot.send_message(
            user.telegram_id,
            f"🎉 Пакет «{product_label}» активирован!",
        )
        return FulfillmentResult(
            purchase_id,
            "ok",
            f"Пакет «{product_label}» активирован",
            user.telegram_id,
        )

    svc = ContentGenerationService(settings, session)
    text = await svc.generate(
        user,
        purchase.product_type,
        version="full",
        partner_birth_date=purchase.partner_birth_date,
        question_text=purchase.question_text,
    )
    text = sanitize_telegram_html(text)
    content = await ContentRepository(session).save(
        user.id,
        purchase.product_type,
        "full",
        text,
        {"purchase_id": purchase.id},
    )
    await bot.send_message(
        user.telegram_id,
        text,
        reply_markup=after_full_keyboard(content.id),
    )
    return FulfillmentResult(
        purchase_id,
        "ok",
        "Полный разбор отправлен пользователю",
        user.telegram_id,
    )


async def reject_purchase(
    bot: Bot,
    session: AsyncSession,
    purchase_id: int,
    *,
    notify_user: bool = True,
) -> FulfillmentResult:
    product_svc = ProductService(session)
    purchase = await product_svc.purchases.get_by_id(purchase_id)
    if not purchase:
        return FulfillmentResult(purchase_id, "error", "Заказ не найден")
    if purchase.status != PurchaseStatus.PENDING:
        return FulfillmentResult(purchase_id, "error", "Можно отклонить только ожидающие заявки")

    await product_svc.purchases.mark_cancelled(purchase)
    user = await UserRepository(session).get_by_id(purchase.user_id)
    if notify_user and user:
        await bot.send_message(
            user.telegram_id,
            "❌ Заявка на оплату не подтверждена. Если ты уже оплатил(а), напиши в поддержку.",
        )
    return FulfillmentResult(
        purchase_id,
        "ok",
        "Заявка отклонена",
        user.telegram_id if user else None,
    )
