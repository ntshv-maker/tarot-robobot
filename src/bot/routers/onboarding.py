from __future__ import annotations

from datetime import date, datetime, time, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import product_menu_keyboard, skip_keyboard
from src.bot.states import OnboardingStates
from src.config import Settings
from src.db.models import ProductType
from src.db.repositories import ContentRepository, ReferralRepository, UserRepository
from src.engines.astro import zodiac_sign
from src.engines.numerology import life_path_number
from src.integrations.kie_client import KieClient
from src.services.content_generation import ContentGenerationService
from src.services.products import EntitlementService
from src.services.referral import ReferralService
from src.utils.telegram_format import sanitize_telegram_html, send_thinking_sticker

router = Router()


def parse_birth_date(text: str) -> date | None:
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_birth_time(text: str) -> time | None:
    for fmt in ("%H:%M", "%H.%M"):
        try:
            return datetime.strptime(text.strip(), fmt).time()
        except ValueError:
            continue
    return None


@router.message(OnboardingStates.name)
async def collect_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = message.text.strip()[:100]
    users = UserRepository(session)
    user = await users.get_by_telegram_id(message.from_user.id)
    if user:
        await users.update_profile(user, name=name, onboarding_step="birth_date")
    await message.answer("📅 Введите дату рождения (ДД.ММ.ГГГГ)\n\nПример: 15.06.1990")
    await state.set_state(OnboardingStates.birth_date)


@router.message(OnboardingStates.birth_date)
async def collect_birth_date(message: Message, state: FSMContext) -> None:
    birth_date = parse_birth_date(message.text or "")
    if not birth_date:
        await message.answer("Не могу распознать дату. Введи в формате ДД.ММ.ГГГГ")
        return
    await state.update_data(birth_date=birth_date.isoformat())
    await message.answer(
        "📅 Введите время рождения (ЧЧ:ММ) или нажмите «Пропустить»",
        reply_markup=skip_keyboard(),
    )
    await state.set_state(OnboardingStates.birth_time)


@router.callback_query(F.data == "onboarding:skip_time")
async def skip_birth_time(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer("📍 Ваше место рождения (город):")
    await state.set_state(OnboardingStates.birth_place)
    await callback.answer()


@router.message(OnboardingStates.birth_time)
async def collect_birth_time(message: Message, state: FSMContext) -> None:
    birth_time = parse_birth_time(message.text or "")
    if birth_time:
        await state.update_data(birth_time=birth_time.isoformat())
    await message.answer("📍 Ваше место рождения (город):")
    await state.set_state(OnboardingStates.birth_place)


@router.message(OnboardingStates.birth_place)
async def collect_birth_place(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    data = await state.get_data()
    birth_date = date.fromisoformat(data["birth_date"])
    birth_time = None
    if data.get("birth_time"):
        birth_time = datetime.fromisoformat(f"2000-01-01T{data['birth_time']}").time()

    zodiac = zodiac_sign(birth_date)
    lp = life_path_number(birth_date)

    users = UserRepository(session)
    user = await users.get_by_telegram_id(message.from_user.id)
    if user:
        await users.update_profile(
            user,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=message.text.strip()[:255],
            zodiac_sign=zodiac.key,
            life_path_number=lp,
            onboarding_step="complete",
            morning_digest_enabled=True,
        )

    await send_thinking_sticker(message, message.bot, settings)
    content_svc = ContentGenerationService(settings, session)
    text = sanitize_telegram_html(
        await content_svc.generate(user, ProductType.NUMEROLOGY_PORTRAIT, version="mini")
    )

    await ContentRepository(session).save(user.id, ProductType.NUMEROLOGY_PORTRAIT, "mini", text, {})
    await message.answer(text)

    followup = (
        f"🌟 ВАШЕ ЧИСЛО ЖИЗНЕННОГО ПУТИ: {lp}\n\n"
        "🎁 Хотите узнать:\n"
        "• Совместимость с партнёром?\n"
        "• Ваш денежный код?\n"
        "• Прогноз на месяц?"
    )
    await message.answer(
        followup,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="💞 Совместимость", callback_data="product:love"),
                    InlineKeyboardButton(text="💰 Денежный код", callback_data="product:wealth"),
                ],
                [InlineKeyboardButton(text="📆 Прогноз на месяц", callback_data="product:forecast_month")],
            ]
        ),
    )

    await ReferralService(settings, users, ReferralRepository(session)).on_referred_user_completed_onboarding(user)
    has_sub = await EntitlementService(session).user_has_any_subscription(user.id)
    await message.answer("Готово! Выбирай тему 👇", reply_markup=product_menu_keyboard(has_subscription=has_sub))
    await state.clear()
