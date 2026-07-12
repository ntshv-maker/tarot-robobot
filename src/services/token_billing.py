from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.db.models import LlmUsageLog


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: Decimal
    cost_rub: Decimal
    input_cost_rub: Decimal
    output_cost_rub: Decimal


def _rub(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_usage_cost(
    prompt_tokens: int,
    completion_tokens: int,
    settings: Settings,
) -> TokenUsage:
    total_tokens = prompt_tokens + completion_tokens
    long_context = prompt_tokens > settings.llm_long_context_threshold

    input_usd_per_1m = (
        settings.llm_input_usd_per_1m_long if long_context else settings.llm_input_usd_per_1m
    )
    output_usd_per_1m = (
        settings.llm_output_usd_per_1m_long if long_context else settings.llm_output_usd_per_1m
    )

    million = Decimal("1000000")
    input_usd = Decimal(prompt_tokens) / million * Decimal(str(input_usd_per_1m))
    output_usd = Decimal(completion_tokens) / million * Decimal(str(output_usd_per_1m))
    total_usd = input_usd + output_usd

    rate = Decimal(str(settings.usd_to_rub_rate))
    input_rub = _rub(input_usd * rate)
    output_rub = _rub(output_usd * rate)
    total_rub = _rub(total_usd * rate)

    return TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=_rub(total_usd),
        cost_rub=total_rub,
        input_cost_rub=input_rub,
        output_cost_rub=output_rub,
    )


class TokenBillingService:
    def __init__(self, settings: Settings, session: AsyncSession | None = None) -> None:
        self.settings = settings
        self.session = session

    async def log_usage(
        self,
        *,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        user_id: int | None = None,
        product_type: str | None = None,
        request_id: str | None = None,
        success: bool = True,
        error: str | None = None,
    ) -> TokenUsage:
        import structlog

        logger = structlog.get_logger("llm.tokens")
        usage = calculate_usage_cost(prompt_tokens, completion_tokens, self.settings)

        logger.info(
            "llm_token_usage",
            model=model,
            user_id=user_id,
            product_type=product_type,
            request_id=request_id,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            input_cost_rub=str(usage.input_cost_rub),
            output_cost_rub=str(usage.output_cost_rub),
            cost_usd=str(usage.cost_usd),
            cost_rub=str(usage.cost_rub),
            usd_to_rub_rate=self.settings.usd_to_rub_rate,
            success=success,
            error=error,
        )

        if self.session is not None:
            row = LlmUsageLog(
                user_id=user_id,
                product_type=product_type,
                model=model,
                request_id=request_id,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                input_cost_rub=float(usage.input_cost_rub),
                output_cost_rub=float(usage.output_cost_rub),
                cost_usd=float(usage.cost_usd),
                cost_rub=float(usage.cost_rub),
                success=success,
                error=error,
            )
            self.session.add(row)
            await self.session.commit()

        return usage
