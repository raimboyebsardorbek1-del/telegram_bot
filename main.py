import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
import os

# konfiguratsiya va initsializatsiya
from config import BOT_TOKEN
from database import init_db

# middlewarelar
from utils import ThrottlingMiddleware, BannedUserMiddleware

# handlerlar (boshqaruvchilar)
from handlers import (
    user_handlers,
    article_handler,
    assignment_handler,
    ai_chat_handler,
    admin_handler
)

async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    # Asosiy loggingni sozlash
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    
    # Ma'lumotlar bazasini asinxron ishga tushirish
    await init_db()

    # Bot va dispetcherni initsializatsiya qilish
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewarelarni ro'yxatga olish (Anti-spam / Throttling)
    dp.message.middleware(ThrottlingMiddleware())
    dp.message.middleware(BannedUserMiddleware())

    # Routerni (yo'naltiruvchi) ro'yxatga olish
    dp.include_router(user_handlers.router)
    dp.include_router(article_handler.router)
    dp.include_router(assignment_handler.router)
    dp.include_router(ai_chat_handler.router)
    dp.include_router(admin_handler.router)

    # Render health check uchun oddiy veb-serverni ishga tushirish
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    try:
        logging.info(f"Veb-server {port} portida ishga tushirilmoqda...")
        await site.start()
        
        logging.info("Bot ishga tushmoqda...")
        # Eski xabarlarni qayta ishlamaslik uchun webhookni o'chirib tozalaymiz
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped successfully!")
