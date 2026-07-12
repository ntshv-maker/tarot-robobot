from __future__ import annotations

from pathlib import Path

import yaml

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def load_prompt(product_type: str, version: str) -> dict[str, str]:
    path = PROMPTS_DIR / product_type / f"{version}.yaml"
    if not path.exists():
        return {
            "system_prompt": "Ты — Лея, эзотерический наставник. Пиши на русском, обращайся на «ты», женский род.",
            "user_prompt_template": "Сгенерируй персональный разбор.\n\nДанные:\n{facts}",
        }
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {
        "system_prompt": data.get("system_prompt", ""),
        "user_prompt_template": data.get("user_prompt_template", ""),
    }


def render_prompt(template: str, facts: dict) -> str:
    result = template
    for key, value in facts.items():
        result = result.replace("{" + key + "}", str(value))
    return result
