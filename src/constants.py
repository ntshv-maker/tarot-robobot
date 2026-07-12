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
}

COMBO_PRODUCTS = {
    ProductType.HAPPY_WOMAN,
}

VIP_INCLUDES_ALL = True
