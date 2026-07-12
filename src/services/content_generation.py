from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.db.models import ProductType, User
from src.engines.astro import moon_phase, zodiac_sign
from src.engines.numerology import (
    LIFE_PATH_ARCHETYPES,
    compatibility_index,
    life_path_number,
    personal_day_number,
    personal_month_number,
    personal_year_number,
    wealth_number,
)
from src.engines.tarot import daily_card, evening_card, weekly_patron, year_arcana
from src.integrations.kie_client import KieClient
from src.services.prompt_loader import load_prompt, render_prompt


class ContentGenerationService:
    def __init__(self, settings: Settings, session: AsyncSession | None = None) -> None:
        self.kie = KieClient(settings, session)

    def compute_facts(
        self,
        user: User,
        product_type: ProductType,
        *,
        version: str = "mini",
        partner_birth_date: date | None = None,
        question_text: str | None = None,
        ref_date: date | None = None,
        parent_content_text: str | None = None,
    ) -> dict:
        ref = ref_date or date.today()
        facts: dict = {
            "name": user.name or user.first_name or "дорогая",
            "birth_date": user.birth_date.strftime("%d.%m.%Y") if user.birth_date else "",
            "birth_place": user.birth_place or "не указано",
            "today": ref.strftime("%d.%m.%Y"),
            "version": version,
        }
        if version == "mini":
            facts["brief_note"] = (
                "ВАЖНО: мини-версия — максимум 3–4 коротких предложения, только суть, без воды."
            )

        if user.birth_date:
            lp = life_path_number(user.birth_date)
            zodiac = zodiac_sign(user.birth_date)
            card = daily_card(user.id, ref)
            facts.update(
                {
                    "life_path_number": lp,
                    "life_path_archetype": LIFE_PATH_ARCHETYPES.get(lp, "Искатель"),
                    "personal_year": personal_year_number(user.birth_date, ref.year),
                    "personal_month": personal_month_number(user.birth_date, ref),
                    "personal_day": personal_day_number(user.birth_date, ref),
                    "wealth_number": wealth_number(user.birth_date),
                    "zodiac_sign": zodiac.name,
                    "zodiac_emoji": zodiac.emoji,
                    "zodiac_element": zodiac.element,
                    "arcana_name": card.name,
                    "arcana_roman": card.roman,
                    "arcana_meaning": f"энергия аркана {card.name}",
                    "year_arcana": year_arcana(user.birth_date, ref.year).name,
                    "moon_phase": moon_phase(ref),
                }
            )

        if partner_birth_date:
            facts["partner_birth_date"] = partner_birth_date.strftime("%d.%m.%Y")
            facts["compatibility_index"] = compatibility_index(user.birth_date, partner_birth_date)

        if question_text:
            facts["question_text"] = question_text

        if parent_content_text:
            facts["parent_content"] = parent_content_text[:3000]

        if product_type == ProductType.WEEKLY_HOROSCOPE:
            from datetime import timedelta

            week_start = ref - timedelta(days=ref.weekday())
            week_end = week_start + timedelta(days=6)
            patron = weekly_patron(user.id, week_start)
            facts["week_range"] = f"{week_start.strftime('%d.%m')} — {week_end.strftime('%d.%m')}"
            facts["week_patron"] = patron.name

        if product_type == ProductType.EVENING_SPREAD:
            ev = evening_card(user.id, ref)
            facts["arcana_name"] = ev.name
            facts["arcana_reversed"] = "да" if ev.reversed else "нет"

        return facts

    async def generate(
        self,
        user: User,
        product_type: ProductType,
        *,
        version: str = "mini",
        partner_birth_date: date | None = None,
        question_text: str | None = None,
        ref_date: date | None = None,
        parent_content_text: str | None = None,
    ) -> str:
        facts = self.compute_facts(
            user,
            product_type,
            version=version,
            partner_birth_date=partner_birth_date,
            question_text=question_text,
            ref_date=ref_date,
            parent_content_text=parent_content_text,
        )
        prompt_data = load_prompt(product_type.value, version)
        user_prompt = render_prompt(prompt_data["user_prompt_template"], facts)
        return await self.kie.chat_completion(
            [
                {"role": "system", "content": prompt_data["system_prompt"]},
                {"role": "user", "content": user_prompt},
            ],
            user_id=user.id,
            product_type=f"{product_type.value}:{version}",
        )
