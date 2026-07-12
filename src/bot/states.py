from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    consent = State()
    name = State()
    birth_date = State()
    birth_time = State()
    birth_place = State()


class ProductStates(StatesGroup):
    partner_birth_date = State()
    question_text = State()
    followup_question = State()
