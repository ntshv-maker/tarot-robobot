#!/usr/bin/env python3
"""Build production .env for VPS from local .env (stdout)."""
from __future__ import annotations

import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL_ENV = ROOT / ".env"

KEEP_PREFIXES = (
    "BOT_TOKEN",
    "KIE_",
    "USD_TO_RUB",
    "LLM_",
    "REFERRAL_BOT_USERNAME",
    "ADMIN_IDS",
    "DASHBOARD_",
    "TIMEZONE",
    "MORNING_",
    "EVENING_",
    "WEEKLY_",
    "PRIVACY_",
    "CONSENT_",
    "OFFER_",
    "TYPING_",
)
SKIP_KEYS = {"DATABASE_URL", "REDIS_URL", "LOCAL_DEV", "DASHBOARD_HOST", "DASHBOARD_PORT"}


def main() -> None:
    postgres_password = os.environ.get("POSTGRES_PASSWORD") or secrets.token_hex(16)
    print(f"POSTGRES_PASSWORD={postgres_password}")
    print("LOCAL_DEV=false")
    print("REDIS_URL=redis://redis:6379/0")
    print("DASHBOARD_HOST=0.0.0.0")
    print("DASHBOARD_PORT=8080")
    print("PYTHONUNBUFFERED=1")

    if not LOCAL_ENV.exists():
        raise SystemExit(f"Missing {LOCAL_ENV}")

    for line in LOCAL_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key in SKIP_KEYS:
            continue
        if any(key.startswith(prefix) for prefix in KEEP_PREFIXES):
            print(f"{key}={value}")


if __name__ == "__main__":
    main()
