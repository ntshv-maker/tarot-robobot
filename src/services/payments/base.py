from __future__ import annotations

from abc import ABC, abstractmethod

from src.db.models import Purchase, User


class PaymentProvider(ABC):
    @abstractmethod
    async def create_payment(self, user: User, purchase: Purchase) -> str:
        """Return payment instructions for user."""

    @abstractmethod
    async def confirm_payment(self, purchase: Purchase) -> bool:
        ...


class ManualPaymentProvider(PaymentProvider):
    async def create_payment(self, user: User, purchase: Purchase) -> str:
        from src.constants import PRODUCT_LABELS, SUBSCRIPTION_PLANS
        from src.db.models import ProductType

        if purchase.product_type == ProductType.PREMIUM:
            months = int(purchase.question_text or "1")
            plan_label = SUBSCRIPTION_PLANS.get(months, {}).get("label", f"{months} мес.")
            product_line = f"Подписка: {plan_label}"
        else:
            product_line = f"Продукт: {PRODUCT_LABELS.get(purchase.product_type, purchase.product_type.value)}"

        return (
            f"💳 Оплата: {purchase.amount_rub} ₽\n"
            f"{product_line}\n\n"
            "Переведите сумму на реквизиты, указанные администратором, "
            "затем нажмите «Я оплатил(а)».\n"
            f"ID заказа: #{purchase.id}"
        )

    async def confirm_payment(self, purchase: Purchase) -> bool:
        return True


class YooKassaProvider(PaymentProvider):
    """Stub for future ЮKassa integration."""

    async def create_payment(self, user: User, purchase: Purchase) -> str:
        raise NotImplementedError("YooKassa integration is planned for v2")

    async def confirm_payment(self, purchase: Purchase) -> bool:
        raise NotImplementedError
