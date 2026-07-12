from __future__ import annotations

import structlog
from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.helpers.telegram import answer_callback, reply_to_callback
from src.bot.keyboards import (
    after_full_keyboard,
    mini_result_keyboard,
    payment_keyboard,
    subscription_plans_keyboard,
)
from src.bot.onboarding_guard import ensure_onboarding_complete
from src.bot.routers.onboarding import parse_birth_date
from src.bot.states import ProductStates
from src.config import Settings
from src.constants import PRODUCT_LABELS, SUBSCRIPTION_PLANS
from src.db.models import ProductType
from src.db.repositories import ContentRepository, UserRepository
from src.services.content_generation import ContentGenerationService
from src.services.payments.base import ManualPaymentProvider
from src.services.products import EntitlementService, ProductService
from src.utils.telegram_format import sanitize_telegram_html, send_thinking_sticker

router = Router()
logger = structlog.get_logger()

PRODUCT_MAP = {
    "love": ProductType.LOVE,
    "wealth": ProductType.WEALTH,
    "negative": ProductType.NEGATIVE,
    "forecast_month": ProductType.FORECAST_MONTH,
    "question": ProductType.QUESTION,
    "happy_woman": ProductType.HAPPY_WOMAN,
    "love_plus": ProductType.LOVE_PLUS,
    "vip": ProductType.VIP,
    "premium": ProductType.PREMIUM,
}

TEXT_TO_PRODUCT = {
    "💞 Любовь": ProductType.LOVE,
    "💰 Деньги": ProductType.WEALTH,
    "🛡️ Негатив": ProductType.NEGATIVE,
    "🔮 Личный прогноз": ProductType.FORECAST_MONTH,
    "💡 Ответ на вопрос": ProductType.QUESTION,
}


async def _require_profile(message: Message, session: AsyncSession):
    user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
    if not await ensure_onboarding_complete(message, user):
        return None
    return user


def _resolve_partner_date(user, data: dict, payload: dict | None = None) -> date | None:
    if data.get("partner_birth_date"):
        return date.fromisoformat(data["partner_birth_date"])
    if payload and payload.get("partner") and payload["partner"] not in {"None", ""}:
        try:
            from datetime import datetime as dt

            return dt.strptime(payload["partner"], "%Y-%m-%d").date()
        except ValueError:
            pass
    return user.partner_birth_date if user else None


def _resolve_question_text(data: dict, payload: dict | None = None) -> str | None:
    if data.get("question_text"):
        return data["question_text"]
    if payload and payload.get("question") and payload["question"] not in {"None", ""}:
        return payload["question"]
    return None


async def _reading_context(
    session: AsyncSession,
    user,
    product: ProductType,
    data: dict,
) -> tuple[date | None, str | None]:
    payload: dict | None = None
    try:
        recent = await ContentRepository(session).get_recent(user.id, product, "mini")
        if recent:
            payload = recent.input_payload or {}
    except Exception:
        pass
    partner_date = _resolve_partner_date(user, data, payload)
    question_text = _resolve_question_text(data, payload)
    return partner_date, question_text


async def _save_partner_date(session: AsyncSession, user, partner_date: date) -> None:
    await UserRepository(session).update_profile(user, partner_birth_date=partner_date)


async def _deliver_full(
    message: Message,
    session: AsyncSession,
    settings: Settings,
    user,
    product: ProductType,
    partner_date: date | None,
    question_text: str | None,
) -> None:
    await send_thinking_sticker(message, message.bot, settings)
    svc = ContentGenerationService(settings, session)
    text = sanitize_telegram_html(
        await svc.generate(
            user,
            product,
            version="full",
            partner_birth_date=partner_date,
            question_text=question_text,
        )
    )
    content = await ContentRepository(session).save(
        user.id,
        product,
        "full",
        text,
        {"partner": str(partner_date), "question": question_text},
    )
    sent = await message.answer(text, reply_markup=after_full_keyboard(content.id))
    content.telegram_message_id = sent.message_id
    await session.commit()


async def _deliver_mini(
    message: Message,
    session: AsyncSession,
    settings: Settings,
    user,
    product: ProductType,
    partner_date: date | None,
    question_text: str | None,
) -> None:
    await message.answer("⏳ Готовлю краткий разбор...")
    await send_thinking_sticker(message, message.bot, settings)
    svc = ContentGenerationService(settings, session)
    text = sanitize_telegram_html(
        await svc.generate(
            user,
            product,
            version="mini",
            partner_birth_date=partner_date,
            question_text=question_text,
        )
    )
    if not text.strip():
        text = "✨ Краткий разбор готов. Нажми «Полный разбор» ниже, чтобы узнать больше."

    await ContentRepository(session).save(
        user.id,
        product,
        "mini",
        text,
        {"partner": str(partner_date), "question": question_text},
    )
    await message.answer(text, reply_markup=mini_result_keyboard(product))


async def _start_reading_flow(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
    user,
    product: ProductType,
) -> None:
    data = await state.get_data()

    if product == ProductType.QUESTION and not data.get("question_text"):
        await message.answer("💬 Напиши свой вопрос одним сообщением:")
        await state.set_state(ProductStates.question_text)
        await state.update_data(product=product.value)
        return

    partner_date = _resolve_partner_date(user, data)
    if product == ProductType.LOVE and not partner_date:
        await message.answer("📅 Введите дату рождения партнёра (ДД.ММ.ГГГГ):")
        await state.set_state(ProductStates.partner_birth_date)
        await state.update_data(pending_product=product.value)
        return

    await _deliver_mini(message, session, settings, user, product, partner_date, data.get("question_text"))
    await state.set_state(None)


async def _handle_full_reading(
    message: Message,
    session: AsyncSession,
    settings: Settings,
    user,
    product: ProductType,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    partner_date, question_text = await _reading_context(session, user, product, data)

    if product == ProductType.QUESTION and not question_text:
        await message.answer("💬 Сначала получи мини-разбор: задай вопрос через меню «💡 Ответ на вопрос».")
        return

    if product == ProductType.LOVE and not partner_date:
        await message.answer("📅 Сначала укажи дату рождения партнёра — выбери «💞 Любовь» в меню.")
        return

    if await EntitlementService(session).has_premium_access(user.id):
        await _deliver_full(message, session, settings, user, product, partner_date, question_text)
        return

    if await EntitlementService(session).has_active_subscription(user.id, product):
        await _deliver_full(message, session, settings, user, product, partner_date, question_text)
        return

    await message.answer(
        "🔓 Полный разбор доступен по подписке.\n\n"
        "Выбери тариф — после оплаты нажми «Полный разбор» снова:",
        reply_markup=subscription_plans_keyboard(product),
    )


@router.message(F.text.in_(list(TEXT_TO_PRODUCT.keys()) + ["✨ Подписка активна"]))
async def product_from_menu(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    user = await _require_profile(message, session)
    if not user:
        return

    if message.text == "✨ Подписка активна":
        await message.answer("✨ У тебя активная подписка! Выбери тему из меню — получишь мини-разбор, затем полный.")
        return

    product = TEXT_TO_PRODUCT[message.text]
    await _start_reading_flow(message, state, session, settings, user, product)


@router.callback_query(F.data.startswith("product:"))
async def product_callback(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if not user or not user.onboarding_complete:
        await callback.message.answer("Сначала пройди регистрацию — нажми /start и заполни анкету.")
        await callback.answer()
        return

    product = PRODUCT_MAP[callback.data.split(":")[1]]
    await _start_reading_flow(callback.message, state, session, settings, user, product)
    await callback.answer()


@router.message(ProductStates.question_text)
async def question_received(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    await state.update_data(question_text=message.text.strip())
    user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
    if not user:
        return
    await _start_reading_flow(message, state, session, settings, user, ProductType.QUESTION)


@router.message(ProductStates.partner_birth_date)
async def partner_date_received(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    partner_date = parse_birth_date(message.text or "")
    if not partner_date:
        await message.answer("Формат: ДД.ММ.ГГГГ")
        return
    await state.update_data(partner_birth_date=partner_date.isoformat())
    data = await state.get_data()
    product = ProductType(data.get("pending_product", "love"))
    user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
    if user:
        await _save_partner_date(session, user, partner_date)

    await _deliver_mini(
        message,
        session,
        settings,
        user,
        product,
        partner_date,
        data.get("question_text"),
    )
    await state.set_state(None)


@router.callback_query(F.data.startswith("full:reading:"))
async def full_reading_callback(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    await answer_callback(callback)
    try:
        product = PRODUCT_MAP[callback.data.split(":")[2]]
    except (IndexError, KeyError):
        await reply_to_callback(callback, "Не удалось распознать тему. Нажми /start.")
        return

    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if not user or not user.onboarding_complete:
        await reply_to_callback(callback, "Сначала пройди регистрацию — /start")
        return

    if callback.message:
        await _handle_full_reading(callback.message, session, settings, user, product, state)


@router.callback_query(F.data.startswith("sub:buy:"))
async def subscription_buy(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await answer_callback(callback)
    try:
        months = int(callback.data.split(":")[2])
        product_key = callback.data.split(":")[3]
        product = PRODUCT_MAP[product_key]
    except (IndexError, KeyError, ValueError):
        await reply_to_callback(callback, "Не удалось оформить подписку. Попробуй снова.")
        return

    if months not in SUBSCRIPTION_PLANS:
        await reply_to_callback(callback, "Такого тарифа нет.")
        return

    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if not user:
        await reply_to_callback(callback, "Сначала /start")
        return

    plan = SUBSCRIPTION_PLANS[months]
    await state.update_data(pending_full_product=product.value)

    purchase = await ProductService(session).create_purchase(
        user,
        ProductType.PREMIUM,
        amount_rub=int(plan["price"]),
        question_text=str(months),
    )
    instructions = await ManualPaymentProvider().create_payment(user, purchase)
    await reply_to_callback(callback, instructions, reply_markup=payment_keyboard(purchase.id))


@router.callback_query(F.data.startswith("gen:mini:"))
async def legacy_gen_mini(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    """Старые кнопки — перенаправляем в новый флоу."""
    await answer_callback(callback)
    try:
        product = PRODUCT_MAP[callback.data.split(":")[2]]
    except (IndexError, KeyError):
        return
    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if user and callback.message:
        await _start_reading_flow(callback.message, state, session, settings, user, product)


@router.callback_query(F.data.startswith("pay:full:"))
async def legacy_pay_full(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    """Старые кнопки оплаты — открываем подписку или полный разбор."""
    await answer_callback(callback)
    try:
        product = PRODUCT_MAP[callback.data.split(":")[2]]
    except (IndexError, KeyError):
        return
    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if user and callback.message:
        await _handle_full_reading(callback.message, session, settings, user, product, state)


@router.callback_query(F.data.startswith("payment:confirm:"))
async def payment_confirm(callback: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    purchase_id = int(callback.data.split(":")[2])
    purchase = await ProductService(session).purchases.get_by_id(purchase_id)
    user = await UserRepository(session).get_by_id(purchase.user_id) if purchase else None
    if not purchase or not user or user.telegram_id != callback.from_user.id:
        await callback.answer("Заказ не найден")
        return

    for admin_id in settings.admin_id_list:
        await callback.bot.send_message(
            admin_id,
            f"💳 Подтверждение оплаты #{purchase.id}\n"
            f"User: {callback.from_user.id}\n"
            f"Product: {purchase.product_type.value}\n"
            f"Amount: {purchase.amount_rub}₽\n\n"
            f"/confirm_payment {purchase.id}",
        )
    await callback.message.answer(
        "✅ Заявка отправлена! После проверки подписка активируется — "
        "нажми «🔓 Полный разбор» под мини-разбором."
    )
    await callback.answer()


@router.callback_query(F.data.startswith("followup:"))
async def followup_question(callback: CallbackQuery, state: FSMContext) -> None:
    content_id = int(callback.data.split(":")[1])
    await state.set_state(ProductStates.followup_question)
    await state.update_data(parent_content_id=content_id)
    await callback.message.answer("💬 Задай вопрос к этому разбору:")
    await callback.answer()


@router.message(ProductStates.followup_question)
async def followup_answer(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    data = await state.get_data()
    parent = await ContentRepository(session).get_by_id(data.get("parent_content_id"))
    user = await UserRepository(session).get_by_telegram_id(message.from_user.id)

    await send_thinking_sticker(message, message.bot, settings)
    svc = ContentGenerationService(settings, session)
    text = sanitize_telegram_html(
        await svc.generate(
            user,
            ProductType.FOLLOWUP,
            version="full",
            question_text=message.text,
            parent_content_text=parent.text if parent else None,
        )
    )
    content = await ContentRepository(session).save(
        user.id,
        ProductType.FOLLOWUP,
        "full",
        text,
        {"parent_id": data.get("parent_content_id"), "question": message.text},
    )
    await message.answer(text, reply_markup=after_full_keyboard(content.id))
    await state.clear()
