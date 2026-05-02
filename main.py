import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
import os

# configurations & initialization
from config import BOT_TOKEN
from database import init_db, get_order, update_order_status

# middlewares
from utils import ThrottlingMiddleware, BannedUserMiddleware

# handlers
from handlers import (
    user_handlers,
    article_handler,
    assignment_handler,
    ai_chat_handler,
    admin_handler,
    report_handler,
    presentation_handler
)

async def handle(request):
    return web.Response(text="Bot is running!")

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

    # Middleware registration
    dp.message.middleware(ThrottlingMiddleware())
    dp.message.middleware(BannedUserMiddleware())

    # Register routers
    dp.include_router(user_handlers.router)
    dp.include_router(article_handler.router)
    dp.include_router(report_handler.router)
    dp.include_router(presentation_handler.router)
    dp.include_router(assignment_handler.router)
    dp.include_router(ai_chat_handler.router)
    dp.include_router(admin_handler.router)

    # Setup web server
    app = web.Application()
    app['bot'] = bot
    app.router.add_get("/", handle)
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    try:
        logging.info(f"Starting web server on port {port}...")
        await site.start()
        
        logging.info("Bot is starting...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped successfully!")
