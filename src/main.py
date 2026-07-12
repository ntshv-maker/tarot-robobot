from __future__ import annotations

import asyncio
import logging
from typing import Any

import structlog
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from src.bot.logging_bot import LoggingBot
from src.bot.middlewares.chat_log import ChatLogMiddleware
from src.bot.middlewares.db import ActivityMiddleware, DbSessionMiddleware
from src.bot.middlewares.settings import SettingsMiddleware
from src.bot.routers import admin, digest, onboarding, packages, products, start
from src.config import get_settings
from src.db.session import async_session_factory, engine
from src.services.scheduler import SchedulerService
from src.utils.memory_redis import MemoryRedis
from src.utils.tarot_image import ensure_tarot_assets

structlog.configure(processors=[structlog.processors.JSONRenderer()])
logger = structlog.get_logger()


async def main() -> None:
    settings = get_settings()
    ensure_tarot_assets()

    bot = LoggingBot(token=settings.bot_token, session_factory=async_session_factory)
    redis: Any
    if settings.use_memory_backend:
        storage = MemoryStorage()
        redis = MemoryRedis()
        logger.info("local_dev_mode", database=settings.database_url, backend="memory")
    else:
        redis = Redis.from_url(settings.redis_url)
        storage = RedisStorage(redis=redis)

    dp = Dispatcher(storage=storage)

    dp.update.middleware(SettingsMiddleware(settings))
    dp.update.middleware(DbSessionMiddleware(async_session_factory))
    dp.update.middleware(ChatLogMiddleware())
    dp.update.middleware(ActivityMiddleware())

    dp.include_router(start.router)
    dp.include_router(onboarding.router)
    dp.include_router(products.router)
    dp.include_router(packages.router)
    dp.include_router(digest.router)
    dp.include_router(admin.router)

    scheduler = SchedulerService(bot, settings, async_session_factory, redis)
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("bot_starting")
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()
        await redis.close()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
