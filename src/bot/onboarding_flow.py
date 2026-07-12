from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from src.bot.keyboards import skip_keyboard
from src.bot.states import OnboardingStates
from src.db.models import User


async def sync_fsm_from_user(state: FSMContext, user: User) -> None:
    data: dict[str, str] = {}
    if user.birth_date:
        data["birth_date"] = user.birth_date.isoformat()
    if user.birth_time:
        data["birth_time"] = user.birth_time.isoformat()
    if data:
        await state.update_data(**data)


async def continue_onboarding(message: Message, state: FSMContext, user: User) -> None:
    if user.name is None:
        await message.answer(
            "Для точного прогноза мне нужны твои данные.\n\n📝 Как тебя зовут?",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(OnboardingStates.name)
        return

    if user.birth_date is None:
        await message.answer(
            f"Продолжим, {user.name}! 📅 Введите дату рождения (ДД.ММ.ГГГГ)\n\nПример: 15.06.1990",
        )
        await state.set_state(OnboardingStates.birth_date)
        return

    if user.birth_place is None:
        if user.onboarding_step == "birth_time" and user.birth_time is None:
            await sync_fsm_from_user(state, user)
            await message.answer(
                "📅 Введите время рождения (ЧЧ:ММ) или нажмите «Пропустить»",
                reply_markup=skip_keyboard(),
            )
            await state.set_state(OnboardingStates.birth_time)
            return

        await sync_fsm_from_user(state, user)
        await message.answer("📍 Ваше место рождения (город):")
        await state.set_state(OnboardingStates.birth_place)
        return
