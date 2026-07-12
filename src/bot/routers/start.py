from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import consent_keyboard, product_menu_keyboard
from src.bot.onboarding_flow import continue_onboarding
from src.bot.states import OnboardingStates
from src.config import Settings
from src.db.repositories import ReferralRepository, UserRepository
from src.services.products import EntitlementService
from src.services.referral import ReferralService

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession, settings: Settings) -> None:
    await state.clear()
    users = UserRepository(session)
    user = await users.get_or_create(
        message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if message.text and " " in message.text:
        arg = message.text.split(maxsplit=1)[1]
        if arg.startswith("ref_"):
            referral = ReferralService(settings, users, ReferralRepository(session))
            await referral.process_start_ref(user, arg[4:])

    if user.onboarding_complete:
        ent = EntitlementService(session)
        has_sub = await ent.user_has_any_subscription(user.id)
        await message.answer(
            f"🔮 С возвращением, {user.name or user.first_name}!\n\nВыбери, что хочешь узнать:",
            reply_markup=product_menu_keyboard(has_subscription=has_sub),
        )
        return

    if user.consent_accepted_at:
        await message.answer(
            f"Продолжим, {user.first_name or 'друг'}! Осталось заполнить несколько данных.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await continue_onboarding(message, state, user)
        return

    await message.answer(
        "🔮 Привет! Я – Лея, и вот что я умею:\n\n"
        "💞 Рассчитать совместимость\n"
        "💰 Понять денежный потенциал\n"
        "🛡️ Есть ли на мне негатив?\n"
        "🔮 Рассчитать личный прогноз на день/месяц/год\n"
        "💡 Помогать в принятии решений\n\n"
        "Перед началом — юридические документы:\n"
        f'• <a href="{settings.privacy_policy_url}">Политика конфиденциальности</a>\n'
        f'• <a href="{settings.consent_url}">Согласие на обработку ПД</a>\n'
        f'• <a href="{settings.offer_url}">Публичная оферта</a>',
        parse_mode="HTML",
        reply_markup=consent_keyboard(),
    )
    await state.set_state(OnboardingStates.consent)


@router.callback_query(F.data == "consent:accept")
async def consent_accept(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

    users = UserRepository(session)
    user = await users.get_by_telegram_id(callback.from_user.id)
    if not user:
        return

    if not user.consent_accepted_at:
        await users.update_profile(user, consent_accepted_at=datetime.now(timezone.utc), onboarding_step="name")

    await continue_onboarding(callback.message, state, user)
