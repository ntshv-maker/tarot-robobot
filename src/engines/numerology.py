from __future__ import annotations

from datetime import date


def reduce_number(n: int, keep_master: bool = True) -> int:
    while n > 9:
        if keep_master and n in (11, 22):
            return n
        n = sum(int(d) for d in str(n))
    return n


def life_path_number(birth_date: date, keep_master: bool = True) -> int:
    digits = f"{birth_date.day:02d}{birth_date.month:02d}{birth_date.year}"
    total = sum(int(d) for d in digits)
    return reduce_number(total, keep_master=keep_master)


def personal_year_number(birth_date: date, year: int | None = None) -> int:
    year = year or date.today().year
    total = birth_date.day + birth_date.month + year
    return reduce_number(total)


def personal_month_number(birth_date: date, ref: date | None = None) -> int:
    ref = ref or date.today()
    total = birth_date.day + birth_date.month + ref.month + ref.year
    return reduce_number(total)


def personal_day_number(birth_date: date, ref: date | None = None) -> int:
    ref = ref or date.today()
    total = birth_date.day + birth_date.month + ref.day + ref.month + ref.year
    return reduce_number(total)


def wealth_number(birth_date: date) -> int:
    """Simplified wealth code from birth date digits."""
    total = birth_date.day * 2 + birth_date.month * 3 + (birth_date.year % 100)
    return reduce_number(total)


def compatibility_index(birth_date_a: date, birth_date_b: date) -> int:
    a = life_path_number(birth_date_a)
    b = life_path_number(birth_date_b)
    return reduce_number(a + b)


LIFE_PATH_ARCHETYPES: dict[int, str] = {
    1: "Лидер",
    2: "Дипломат",
    3: "Творец",
    4: "Строитель",
    5: "Искатель",
    6: "Хранитель",
    7: "Мудрец",
    8: "Достигатор",
    9: "Гуманист",
    11: "Вдохновитель",
    22: "Мастер-строитель",
}
