from datetime import date

from src.engines.astro import zodiac_sign
from src.engines.numerology import (
    compatibility_index,
    life_path_number,
    personal_day_number,
    personal_year_number,
    reduce_number,
    wealth_number,
)
from src.engines.tarot import daily_card, year_arcana


def test_life_path_number():
    assert life_path_number(date(1990, 6, 15)) == reduce_number(1 + 5 + 0 + 6 + 1 + 9 + 9 + 0)


def test_personal_year_number():
    result = personal_year_number(date(1990, 6, 15), 2026)
    assert 1 <= result <= 9 or result in (11, 22)


def test_wealth_number_range():
    w = wealth_number(date(1985, 3, 22))
    assert 1 <= w <= 9 or w in (11, 22)


def test_compatibility_index():
    a = date(1990, 6, 15)
    b = date(1988, 12, 1)
    idx = compatibility_index(a, b)
    assert 1 <= idx <= 9 or idx in (11, 22)


def test_zodiac_sign():
    assert zodiac_sign(date(1990, 6, 15)).name == "Близнецы"
    assert zodiac_sign(date(1990, 1, 10)).name == "Козерог"


def test_daily_card_deterministic():
    d1 = daily_card(42, date(2026, 7, 11))
    d2 = daily_card(42, date(2026, 7, 11))
    d3 = daily_card(42, date(2026, 7, 12))
    assert d1.index == d2.index
    assert 0 <= d1.index <= 21
    assert d1.name == d2.name


def test_year_arcana():
    card = year_arcana(date(1990, 6, 15), 2026)
    assert 0 <= card.index <= 21


def test_personal_day_number():
    n = personal_day_number(date(1990, 6, 15), date(2026, 7, 11))
    assert 1 <= n <= 9 or n in (11, 22)
