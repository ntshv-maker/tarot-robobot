from __future__ import annotations

from src.db.models import ProductType

PRODUCT_PRICES: dict[ProductType, int] = {
    ProductType.LOVE: 550,
    ProductType.FORECAST_MONTH: 550,
    ProductType.WEALTH: 390,
    ProductType.NEGATIVE: 300,
    ProductType.QUESTION: 500,
    ProductType.HAPPY_WOMAN: 990,
    ProductType.LOVE_PLUS: 1200,
    ProductType.VIP: 2300,
    ProductType.PREMIUM: 499,
}

PRODUCT_LABELS: dict[ProductType, str] = {
    ProductType.LOVE: "💞 Любовь",
    ProductType.FORECAST_MONTH: "🔮 Личный прогноз",
    ProductType.WEALTH: "💰 Деньги",
    ProductType.NEGATIVE: "🛡️ Негатив",
    ProductType.QUESTION: "💡 Ответ на вопрос",
    ProductType.HAPPY_WOMAN: "🎁 Счастливая женщина",
    ProductType.LOVE_PLUS: "💗 ЛЮБОВЬ+",
    ProductType.VIP: "👑 VIP-пакет",
    ProductType.PREMIUM: "✨ Подписка на полные разборы",
}

SUBSCRIPTION_PLANS: dict[int, dict[str, int | str]] = {
    1: {"months": 1, "days": 30, "price": 499, "label": "1 месяц — 499₽"},
    2: {"months": 2, "days": 60, "price": 849, "label": "2 месяца — 849₽"},
    3: {"months": 3, "days": 90, "price": 1499, "label": "3 месяца — 1499₽"},
}

ONE_TIME_PRODUCTS = {
    ProductType.LOVE,
    ProductType.FORECAST_MONTH,
    ProductType.WEALTH,
    ProductType.NEGATIVE,
    ProductType.QUESTION,
}

SUBSCRIPTION_PRODUCTS = {
    ProductType.LOVE_PLUS,
    ProductType.VIP,
    ProductType.PREMIUM,
}

COMBO_PRODUCTS = {
    ProductType.HAPPY_WOMAN,
}

VIP_INCLUDES_ALL = True

READING_PRODUCTS = ONE_TIME_PRODUCTS
