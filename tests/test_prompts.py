from __future__ import annotations

from src.services.prompt_loader import load_prompt, render_prompt


def test_load_prompt_love_mini():
    data = load_prompt("love", "mini")
    assert "Лея" in data["system_prompt"] or "love" in data["user_prompt_template"] or data["system_prompt"]


def test_render_prompt():
    template = "Привет, {name}! Число: {life_path_number}"
    result = render_prompt(template, {"name": "Аня", "life_path_number": 4})
    assert "Аня" in result
    assert "4" in result
