from __future__ import annotations

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.services.token_billing import TokenBillingService

logger = structlog.get_logger()


class KieClient:
    def __init__(self, settings: Settings, session: AsyncSession | None = None) -> None:
        self.settings = settings
        self.billing = TokenBillingService(settings, session)

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.8,
        user_id: int | None = None,
        product_type: str | None = None,
    ) -> str:
        if not self.settings.kie_api_key:
            logger.warning("kie_api_missing_key", user_id=user_id, product_type=product_type)
            return self._fallback_response(messages)

        headers = {
            "Authorization": f"Bearer {self.settings.kie_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.kie_model,
            "messages": messages,
            "stream": False,
            "reasoning_effort": self.settings.kie_reasoning_effort,
        }
        if temperature != 0.8:
            payload["temperature"] = temperature

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(self.settings.kie_api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                usage = data.get("usage") or {}
                prompt_tokens = int(usage.get("prompt_tokens") or 0)
                completion_tokens = int(usage.get("completion_tokens") or 0)
                total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
                request_id = data.get("id")

                await self.billing.log_usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model=data.get("model") or self.settings.kie_model,
                    user_id=user_id,
                    product_type=product_type,
                    request_id=request_id,
                    success=True,
                )

                logger.info(
                    "kie_chat_completion_ok",
                    request_id=request_id,
                    user_id=user_id,
                    product_type=product_type,
                    total_tokens=total_tokens,
                )
                return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.warning(
                "kie_api_failed",
                error=str(exc),
                user_id=user_id,
                product_type=product_type,
            )
            await self.billing.log_usage(
                prompt_tokens=0,
                completion_tokens=0,
                model=self.settings.kie_model,
                user_id=user_id,
                product_type=product_type,
                success=False,
                error=str(exc),
            )
            return self._fallback_response(messages)

    def _fallback_response(self, messages: list[dict[str, str]]) -> str:
        user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return (
            "✨ Персональный разбор временно сформирован в офлайн-режиме.\n\n"
            f"{user_msg[:500]}\n\n"
            "⭐ СОВЕТ ОТ ЛЕИ: Доверься своей интуиции — она уже знает ответ."
        )
