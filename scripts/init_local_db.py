#!/usr/bin/env python3
"""Create SQLite tables for local development (no Docker / no PostgreSQL)."""
from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine

from src.config import get_settings
from src.db.models import Base


async def main() -> None:
    settings = get_settings()
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    if db_path.startswith("./"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print(f"OK: tables created at {settings.database_url}")


if __name__ == "__main__":
    asyncio.run(main())
