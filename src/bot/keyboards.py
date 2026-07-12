from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from src.constants import PRODUCT_LABELS, SUBSCRIPTION_PLANS
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
    ]
    if has_subscription:
        rows.append([KeyboardButton(text="✨ Подписка активна")])
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


def mini_result_keyboard(product: ProductType) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔓 Полный разбор", callback_data=f"full:reading:{product.value}")],
        ]
    )


def subscription_plans_keyboard(product: ProductType) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=str(SUBSCRIPTION_PLANS[1]["label"]),
                    callback_data=f"sub:buy:1:{product.value}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=str(SUBSCRIPTION_PLANS[2]["label"]),
                    callback_data=f"sub:buy:2:{product.value}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=str(SUBSCRIPTION_PLANS[3]["label"]),
                    callback_data=f"sub:buy:3:{product.value}",
                )
            ],
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
            ]
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
