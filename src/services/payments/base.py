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
        return (
            f"💳 Оплата: {purchase.amount_rub} ₽\n"
            f"Продукт: {purchase.product_type.value}\n\n"
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
