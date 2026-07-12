from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import PRODUCT_PRICES
from src.db.models import ProductType, User
from src.db.repositories import PurchaseRepository, SubscriptionRepository, UserRepository


class EntitlementService:
    def __init__(self, session: AsyncSession) -> None:
        self.purchases = PurchaseRepository(session)
        self.subscriptions = SubscriptionRepository(session)

    async def has_active_subscription(self, user_id: int, product_type: ProductType) -> bool:
        active = await self.subscriptions.get_active(user_id)
        for sub in active:
            if sub.product_type == ProductType.VIP:
                return True
            if sub.product_type == product_type:
                return True
            if sub.product_type == ProductType.HAPPY_WOMAN and product_type in {
                ProductType.LOVE,
                ProductType.WEALTH,
                ProductType.FORECAST_MONTH,
            }:
                return True
            if sub.product_type == ProductType.LOVE_PLUS and product_type == ProductType.LOVE:
                return True
        return False

    async def can_use_full(self, user: User, product_type: ProductType) -> bool:
        if await self.has_active_subscription(user.id, product_type):
            return True
        return await self.purchases.has_paid_product(user.id, product_type)

    async def get_active_subscription_types(self, user_id: int) -> list[ProductType]:
        subs = await self.subscriptions.get_active(user_id)
        return [s.product_type for s in subs]

    async def user_has_any_subscription(self, user_id: int) -> bool:
        return bool(await self.subscriptions.get_active(user_id))


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.subscriptions = SubscriptionRepository(session)

    async def activate(self, user_id: int, product_type: ProductType, days: int = 30) -> None:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=days)
        await self.subscriptions.create(user_id, product_type, now, expires)


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.purchases = PurchaseRepository(session)
        self.entitlements = EntitlementService(session)
        self.subscriptions = SubscriptionService(session)

    def price_for(self, product_type: ProductType, user: User) -> int:
        base = PRODUCT_PRICES[product_type]
        if user.referral_discount_percent:
            return int(base * (100 - user.referral_discount_percent) / 100)
        return base

    async def create_purchase(
        self,
        user: User,
        product_type: ProductType,
        *,
        partner_birth_date=None,
        question_text: str | None = None,
    ):
        amount = self.price_for(product_type, user)
        return await self.purchases.create(
            user.id,
            product_type,
            amount,
            partner_birth_date=partner_birth_date,
            question_text=question_text,
        )

    async def fulfill_purchase(self, purchase) -> None:
        await self.purchases.mark_paid(purchase)
        user = await UserRepository(self.session).get_by_id(purchase.user_id)
        if user and user.referral_discount_percent:
            user.referral_discount_percent = 0
            await self.session.commit()

        if purchase.product_type in {ProductType.LOVE_PLUS, ProductType.VIP}:
            await self.subscriptions.activate(purchase.user_id, purchase.product_type)
        elif purchase.product_type == ProductType.HAPPY_WOMAN:
            await self.subscriptions.activate(purchase.user_id, ProductType.HAPPY_WOMAN)
