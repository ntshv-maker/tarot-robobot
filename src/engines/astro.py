from __future__ import annotations

from dataclasses import dataclass
from datetime import date

ZODIAC_SIGNS = [
    ("capricorn", "Козерог", "♑", (12, 22), (1, 19)),
    ("aquarius", "Водолей", "♒", (1, 20), (2, 18)),
    ("pisces", "Рыбы", "♓", (2, 19), (3, 20)),
    ("aries", "Овен", "♈", (3, 21), (4, 19)),
    ("taurus", "Телец", "♉", (4, 20), (5, 20)),
    ("gemini", "Близнецы", "♊", (5, 21), (6, 20)),
    ("cancer", "Рак", "♋", (6, 21), (7, 22)),
    ("leo", "Лев", "♌", (7, 23), (8, 22)),
    ("virgo", "Дева", "♍", (8, 23), (9, 22)),
    ("libra", "Весы", "♎", (9, 23), (10, 22)),
    ("scorpio", "Скорпион", "♏", (10, 23), (11, 21)),
    ("sagittarius", "Стрелец", "♐", (11, 22), (12, 21)),
]

ELEMENTS = {
    "aries": "огонь",
    "leo": "огонь",
    "sagittarius": "огонь",
    "taurus": "земля",
    "virgo": "земля",
    "capricorn": "земля",
    "gemini": "воздух",
    "libra": "воздух",
    "aquarius": "воздух",
    "cancer": "вода",
    "scorpio": "вода",
    "pisces": "вода",
}


@dataclass
class ZodiacInfo:
    key: str
    name: str
    emoji: str
    element: str


def _in_range(month: int, day: int, start: tuple[int, int], end: tuple[int, int]) -> bool:
    sm, sd = start
    em, ed = end
    current = month * 100 + day
    start_val = sm * 100 + sd
    end_val = em * 100 + ed
    if start_val <= end_val:
        return start_val <= current <= end_val
    return current >= start_val or current <= end_val


def zodiac_sign(birth_date: date) -> ZodiacInfo:
    for key, name, emoji, start, end in ZODIAC_SIGNS:
        if _in_range(birth_date.month, birth_date.day, start, end):
            return ZodiacInfo(key=key, name=name, emoji=emoji, element=ELEMENTS[key])
    return ZodiacInfo(key="capricorn", name="Козерог", emoji="♑", element="земля")


def moon_phase(ref: date | None = None) -> str:
    """Simplified moon phase label."""
    ref = ref or date.today()
    # Approximate synodic cycle
    known_new_moon = date(2000, 1, 6)
    days = (ref - known_new_moon).days
    phase = (days % 29.53) / 29.53
    if phase < 0.125 or phase >= 0.875:
        return "новолуние"
    if phase < 0.375:
        return "растущая луна"
    if phase < 0.625:
        return "полнолуние"
    return "убывающая луна"
