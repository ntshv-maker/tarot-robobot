from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from src.constants import PRODUCT_LABELS, PRODUCT_PRICES
from src.db.models import ProductType


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Соглашаюсь", callback_data="consent:accept")]]
    )


def skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⏭ Пропустить", callback_data="onboarding:skip_time")]]
    )


def product_menu_keyboard(has_subscription: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [
            KeyboardButton(text="💞 Любовь"),
            KeyboardButton(text="💰 Деньги"),
            KeyboardButton(text="🛡️ Негатив"),
        ],
        [
            KeyboardButton(text="🔮 Личный прогноз"),
            KeyboardButton(text="💡 Ответ на вопрос"),
        ],
        [KeyboardButton(text="📦 Тарифы и пакеты")],
    ]
    if has_subscription:
        rows.append([KeyboardButton(text="▶️ Запустить")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def product_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💞 Любовь", callback_data="product:love"),
                InlineKeyboardButton(text="💰 Деньги", callback_data="product:wealth"),
            ],
            [
                InlineKeyboardButton(text="🛡️ Негатив", callback_data="product:negative"),
                InlineKeyboardButton(text="🔮 Личный прогноз", callback_data="product:forecast_month"),
            ],
            [InlineKeyboardButton(text="💡 Ответ на вопрос", callback_data="product:question")],
        ]
    )


def mini_full_keyboard(product: ProductType) -> InlineKeyboardMarkup:
    price = PRODUCT_PRICES[product]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🆓 Бесплатная версия", callback_data=f"gen:mini:{product.value}"),
                InlineKeyboardButton(text=f"🔓 Полная версия — {price}₽", callback_data=f"pay:full:{product.value}"),
            ]
        ]
    )


def payment_keyboard(purchase_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я оплатил(а)", callback_data=f"payment:confirm:{purchase_id}")],
        ]
    )


def after_full_keyboard(content_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Задать вопрос к разбору",
                    callback_data=f"followup:{content_id}",
                ),
                InlineKeyboardButton(text="📦 Тарифы и пакеты", callback_data="packages:show"),
            ]
        ]
    )


def packages_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Счастливая женщина — 990₽", callback_data="pay:full:happy_woman")],
            [InlineKeyboardButton(text="💗 ЛЮБОВЬ+ — 1200₽/мес", callback_data="pay:full:love_plus")],
            [InlineKeyboardButton(text="👑 VIP — 2300₽/мес", callback_data="pay:full:vip")],
        ]
    )


def digest_opt_in_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📬 Да, присылай!", callback_data="digest:enable"),
                InlineKeyboardButton(text="🚫 Нет, спасибо", callback_data="digest:disable"),
            ]
        ]
    )


def funnel_day2_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❤️ Отношения", callback_data="funnel:love"),
                InlineKeyboardButton(text="💰 Деньги", callback_data="funnel:wealth"),
            ],
            [InlineKeyboardButton(text="🔮 Просто совет", callback_data="funnel:advice")],
        ]
    )


def evening_spread_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🌙 Вечерний расклад", callback_data="evening:spread")]]
    )


def another_advice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Другой совет", callback_data="daily:another_advice")],
            [
                InlineKeyboardButton(text="💞 Совместимость", callback_data="product:love"),
                InlineKeyboardButton(text="💰 Денежный код", callback_data="product:wealth"),
            ],
        ]
    )
