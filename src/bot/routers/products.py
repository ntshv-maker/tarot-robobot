from __future__ import annotations

from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import (
    after_full_keyboard,
    mini_full_keyboard,
    packages_keyboard,
    payment_keyboard,
    product_menu_keyboard,
)
from src.bot.onboarding_guard import ensure_onboarding_complete
from src.bot.routers.onboarding import parse_birth_date
from src.bot.states import ProductStates
from src.config import Settings
from src.constants import PRODUCT_LABELS, PRODUCT_PRICES
from src.db.models import ProductType
from src.db.repositories import ContentRepository, UserRepository
from src.services.content_generation import ContentGenerationService
from src.services.payments.base import ManualPaymentProvider
from src.services.products import EntitlementService, ProductService
from src.utils.telegram_format import sanitize_telegram_html, send_thinking_sticker

router = Router()

PRODUCT_MAP = {
    "love": ProductType.LOVE,
    "wealth": ProductType.WEALTH,
    "negative": ProductType.NEGATIVE,
    "forecast_month": ProductType.FORECAST_MONTH,
    "question": ProductType.QUESTION,
    "happy_woman": ProductType.HAPPY_WOMAN,
    "love_plus": ProductType.LOVE_PLUS,
    "vip": ProductType.VIP,
}

TEXT_TO_PRODUCT = {
    "💞 Любовь": ProductType.LOVE,
    "💰 Деньги": ProductType.WEALTH,
    "🛡️ Негатив": ProductType.NEGATIVE,
    "🔮 Личный прогноз": ProductType.FORECAST_MONTH,
    "💡 Ответ на вопрос": ProductType.QUESTION,
}

PRODUCT_DESCRIPTIONS = {
    ProductType.LOVE: (
        "❤️ «Любовь» — 550₽\n\n"
        "Узнай, что происходит в вашей паре: мысли партнёра, чувства, конфликты, кармическая связь.\n\n"
        "✔️ Перестанешь гадать — начнёшь понимать."
    ),
    ProductType.FORECAST_MONTH: (
        "📆 «Личный прогноз на месяц» — 550₽\n\n"
        "Что готовит ближайший месяц в любви, деньгах и здоровье?\n\n"
        "✔️ Будешь на шаг впереди событий."
    ),
    ProductType.WEALTH: (
        "💰 «Код богатства» — 390₽\n\n"
        "Твой денежный код, «чёрные дыры» и лучшие сферы заработка.\n\n"
        "✔️ Деньги начнут приходить легче."
    ),
    ProductType.NEGATIVE: (
        "🛡️ «Есть ли на мне негатив?» — 300₽\n\n"
        "Энергетическая диагностика 5 сфер жизни.\n\n"
        "⚠️ Это инструмент самопознания, не медицинский диагноз."
    ),
    ProductType.QUESTION: (
        "💡 «Ответ на вопрос» — 500₽\n\n"
        "Задай любой вопрос — карты подскажут, что делать дальше."
    ),
}


async def _require_profile(message: Message, session: AsyncSession):
    user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
    if not await ensure_onboarding_complete(message, user):
        return None
    return user


async def _send_product_pitch(message: Message, product: ProductType) -> None:
    desc = PRODUCT_DESCRIPTIONS.get(product, PRODUCT_LABELS[product])
    await message.answer(desc, reply_markup=mini_full_keyboard(product))


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


@router.message(F.text.in_(list(TEXT_TO_PRODUCT.keys()) + ["📦 Тарифы и пакеты", "▶️ Запустить"]))
async def product_from_menu(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await _require_profile(message, session)
    if not user:
        return

    if message.text == "📦 Тарифы и пакеты":
        await message.answer("📦 КОМБО-ПАКЕТЫ:", reply_markup=packages_keyboard())
        return

    if message.text == "▶️ Запустить":
        subs = await EntitlementService(session).get_active_subscription_types(user.id)
        if ProductType.VIP in subs:
            await message.answer("👑 VIP активен! Выбери любую тему из меню.")
        elif ProductType.LOVE_PLUS in subs:
            await _send_product_pitch(message, ProductType.LOVE)
        else:
            await message.answer("Выбери тему из меню 👇")
        return

    product = TEXT_TO_PRODUCT[message.text]
    if product == ProductType.QUESTION:
        await message.answer("💬 Напиши свой вопрос одним сообщением:")
        await state.set_state(ProductStates.question_text)
        await state.update_data(product=product.value)
        return
    await _send_product_pitch(message, product)


@router.callback_query(F.data.startswith("product:"))
async def product_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if not user or not user.onboarding_complete:
        await callback.message.answer("Сначала пройди регистрацию — нажми /start и заполни анкету.")
        await callback.answer()
        return

    product = PRODUCT_MAP[callback.data.split(":")[1]]
    if product == ProductType.QUESTION:
        await callback.message.answer("💬 Напиши свой вопрос одним сообщением:")
        await state.set_state(ProductStates.question_text)
        await state.update_data(product=product.value)
    else:
        await _send_product_pitch(callback.message, product)
    await callback.answer()


@router.message(ProductStates.question_text)
async def question_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.update_data(question_text=message.text.strip())
    await _send_product_pitch(message, ProductType.QUESTION)
    await state.set_state(None)


@router.callback_query(F.data.startswith("gen:mini:"))
async def generate_mini(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    product = PRODUCT_MAP[callback.data.split(":")[2]]
    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала /start")
        return

    data = await state.get_data()
    partner_date = date.fromisoformat(data["partner_birth_date"]) if data.get("partner_birth_date") else None

    if product == ProductType.LOVE and not partner_date:
        await callback.message.answer("📅 Введите дату рождения партнёра (ДД.ММ.ГГГГ):")
        await state.set_state(ProductStates.partner_birth_date)
        await state.update_data(pending_product=product.value)
        await callback.answer()
        return

    cached = await ContentRepository(session).get_recent(user.id, product, "mini")
    if cached:
        await callback.message.answer(cached.text, reply_markup=mini_full_keyboard(product))
        await callback.message.answer("📦 КОМБО-ПАКЕТЫ:", reply_markup=packages_keyboard())
        await callback.answer()
        return

    await send_thinking_sticker(callback.message, callback.bot, settings)
    svc = ContentGenerationService(settings, session)
    text = sanitize_telegram_html(
        await svc.generate(
            user,
            product,
            version="mini",
            partner_birth_date=partner_date,
            question_text=data.get("question_text"),
        )
    )
    await ContentRepository(session).save(
        user.id,
        product,
        "mini",
        text,
        {"partner": str(partner_date), "question": data.get("question_text")},
    )
    await callback.message.answer(text, reply_markup=mini_full_keyboard(product))
    await callback.message.answer("📦 КОМБО-ПАКЕТЫ:", reply_markup=packages_keyboard())
    await callback.answer()


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

    if await EntitlementService(session).can_use_full(user, product):
        await _deliver_full(message, session, settings, user, product, partner_date, data.get("question_text"))
        await state.clear()
        return

    await send_thinking_sticker(message, message.bot, settings)
    svc = ContentGenerationService(settings, session)
    text = sanitize_telegram_html(await svc.generate(user, product, version="mini", partner_birth_date=partner_date))
    await message.answer(text, reply_markup=mini_full_keyboard(product))
    await message.answer("📦 КОМБО-ПАКЕТЫ:", reply_markup=packages_keyboard())
    await state.set_state(None)


@router.callback_query(F.data.startswith("pay:full:"))
async def pay_full(callback: CallbackQuery, state: FSMContext, session: AsyncSession, settings: Settings) -> None:
    product = PRODUCT_MAP[callback.data.split(":")[2]]
    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    data = await state.get_data()
    partner_date = date.fromisoformat(data["partner_birth_date"]) if data.get("partner_birth_date") else None

    if await EntitlementService(session).can_use_full(user, product):
        await _deliver_full(callback.message, session, settings, user, product, partner_date, data.get("question_text"))
        await callback.answer("У вас уже есть доступ!")
        return

    purchase = await ProductService(session).create_purchase(
        user,
        product,
        partner_birth_date=partner_date,
        question_text=data.get("question_text"),
    )
    instructions = await ManualPaymentProvider().create_payment(user, purchase)
    await callback.message.answer(instructions, reply_markup=payment_keyboard(purchase.id))
    await callback.answer()


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
    await callback.message.answer("✅ Заявка отправлена! После проверки ты получишь полный разбор.")
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
