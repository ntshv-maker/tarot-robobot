from __future__ import annotations

import pytest

from src.config import Settings
from src.services.token_billing import calculate_usage_cost


@pytest.fixture
def settings() -> Settings:
    return Settings(
        BOT_TOKEN="test",
        USD_TO_RUB_RATE=100.0,
        LLM_INPUT_USD_PER_1M=1.25,
        LLM_OUTPUT_USD_PER_1M=10.0,
    )


def test_token_cost_rub_conversion(settings: Settings):
    usage = calculate_usage_cost(prompt_tokens=1000, completion_tokens=500, settings=settings)
    assert usage.prompt_tokens == 1000
    assert usage.completion_tokens == 500
    assert usage.total_tokens == 1500
    assert usage.cost_rub > 0
    # input: 1000/1e6 * 1.25 * 100 = 0.125 RUB
    assert float(usage.input_cost_rub) == pytest.approx(0.125, rel=1e-3)
    # output: 500/1e6 * 10 * 100 = 0.5 RUB
    assert float(usage.output_cost_rub) == pytest.approx(0.5, rel=1e-3)
    assert float(usage.cost_rub) == pytest.approx(0.625, rel=1e-3)
