import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# configurations & initialization
from config import BOT_TOKEN
from database import init_db

# middlewares
from utils import ThrottlingMiddleware, BannedUserMiddleware

# handlers
from handlers import (
    user_handlers,
    article_handler,
    assignment_handler,
    ai_chat_handler,
    admin_handler
)

async def main():
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    
    # Initialize the database asynchronously
    await init_db()

    # Initialize bot and dispatchers
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware registration (Anti-spam / Throttling)
    dp.message.middleware(ThrottlingMiddleware())
    dp.message.middleware(BannedUserMiddleware())

    # Register routers (order is somewhat important but generally handled by filters)
    dp.include_router(user_handlers.router)
    dp.include_router(article_handler.router)
    dp.include_router(assignment_handler.router)
    dp.include_router(ai_chat_handler.router)
    dp.include_router(admin_handler.router)

    # Start polling safely
    try:
        logging.info("Bot is starting...")
        # Drop previous updates to avoid processing stale messages
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped successfully!")
