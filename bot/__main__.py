import asyncio
import logging
import sys
from bot.core.loader import bot, dp, settings
from bot.core.database import engine, Base
from bot.middlewares import AuthMiddleware, ChatManagementMiddleware
from bot.handlers.admin import menu, filters, settings as admin_settings, stats, logs
from bot.handlers.moderation import messages
from bot.handlers import events

async def on_startup():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database initialized")

async def main():
    logging.basicConfig(level=settings.LOG_LEVEL, stream=sys.stdout)
    
    # Register Middlewares
    dp.message.middleware(ChatManagementMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Register Routers
    dp.include_router(events.router)
    dp.include_router(menu.router)
    dp.include_router(filters.router)
    dp.include_router(admin_settings.router)
    dp.include_router(stats.router)
    dp.include_router(logs.router)
    dp.include_router(messages.router)

    # Startup
    await on_startup()
    
    logging.info("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
