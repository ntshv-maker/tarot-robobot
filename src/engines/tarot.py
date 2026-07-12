from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ARCANA_NAMES = [
    "Шут",
    "Маг",
    "Жрица",
    "Императрица",
    "Император",
    "Иерофант",
    "Влюблённые",
    "Колесница",
    "Сила",
    "Отшельник",
    "Колесо Фортуны",
    "Справедливость",
    "Повешенный",
    "Смерть",
    "Умеренность",
    "Дьявол",
    "Башня",
    "Звезда",
    "Луна",
    "Солнце",
    "Суд",
    "Мир",
]

ROMAN_NUMERALS = [
    "0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI",
]


@dataclass
class TarotCard:
    index: int
    name: str
    roman: str
    reversed: bool = False

    @property
    def display_name(self) -> str:
        suffix = " (перевёрнутая)" if self.reversed else ""
        return f"{self.name.upper()} ({self.roman} аркан){suffix}"


def _seed_index(seed: str, modulo: int = 22) -> int:
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return int(digest, 16) % modulo


def daily_card(user_id: int, ref: date | None = None) -> TarotCard:
    ref = ref or date.today()
    idx = _seed_index(f"{user_id}:{ref.isoformat()}")
    return TarotCard(index=idx, name=ARCANA_NAMES[idx], roman=ROMAN_NUMERALS[idx])


def year_arcana(birth_date: date, year: int | None = None) -> TarotCard:
    year = year or date.today().year
    total = birth_date.day + birth_date.month + (year % 100)
    idx = _seed_index(str(total)) if total >= 22 else total % 22
    return TarotCard(index=idx, name=ARCANA_NAMES[idx], roman=ROMAN_NUMERALS[idx])


def evening_card(user_id: int, ref: date | None = None) -> TarotCard:
    card = daily_card(user_id, ref)
    reversed_flag = _seed_index(f"rev:{user_id}:{ref or date.today()}") % 2 == 1
    return TarotCard(index=card.index, name=card.name, roman=card.roman, reversed=reversed_flag)


def weekly_patron(user_id: int, week_start: date) -> TarotCard:
    idx = _seed_index(f"week:{user_id}:{week_start.isoformat()}")
    return TarotCard(index=idx, name=ARCANA_NAMES[idx], roman=ROMAN_NUMERALS[idx])


def card_image_path(index: int, assets_dir: Path | None = None) -> Path:
    assets_dir = assets_dir or Path(__file__).resolve().parents[2] / "assets" / "tarot"
    return assets_dir / f"{index:02d}.png"
