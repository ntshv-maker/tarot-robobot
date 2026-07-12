from __future__ import annotations

from src.config import Settings
from src.db.repositories import ReferralRepository, UserRepository


class ReferralService:
    def __init__(self, settings: Settings, users: UserRepository, referrals: ReferralRepository) -> None:
        self.settings = settings
        self.users = users
        self.referrals = referrals

    def referral_link(self, user) -> str:
        username = self.settings.referral_bot_username or "bot"
        return f"https://t.me/{username}?start=ref_{user.referral_code}"

    async def process_start_ref(self, user, ref_code: str) -> None:
        referrer = await self.users.get_by_referral_code(ref_code)
        if not referrer or referrer.id == user.id or user.referred_by_user_id:
            return
        await self.users.update_profile(user, referred_by_user_id=referrer.id)
        await self.referrals.create(referrer.id, user.id)

    async def on_referred_user_completed_onboarding(self, user) -> None:
        if not user.referred_by_user_id:
            return
        await self.referrals.activate_reward(user.referred_by_user_id, user.id)
