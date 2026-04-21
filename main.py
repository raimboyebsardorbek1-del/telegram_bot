import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
import os

# configurations & initialization
from config import BOT_TOKEN, WEBHOOK_SECRET, SUBSCRIPTION_DAYS
from database import init_db, get_payment, update_payment_status, add_user_subscription

# middlewares
from utils import ThrottlingMiddleware, BannedUserMiddleware

# handlers
from handlers import (
    user_handlers,
    article_handler,
    assignment_handler,
    ai_chat_handler,
    admin_handler,
    payment_handler
)

async def handle(request):
    return web.Response(text="Bot is running!")

async def payment_webhook(request):
    try:
        data = await request.json()
        
        # Security check
        signature = data.get("signature")
        if signature != WEBHOOK_SECRET:
            return web.Response(status=403, text="Invalid signature")
            
        payment_id = data.get("payment_id")
        status = data.get("status")
        
        if not payment_id or status != "paid":
            return web.Response(status=400, text="Invalid data")
            
        # Get payment
        payment = await get_payment(payment_id)
        if not payment:
            return web.Response(status=404, text="Payment not found")
            
        if payment['status'] == 'paid':
            return web.Response(status=200, text="Already paid")
            
        # Mark as paid
        await update_payment_status(payment_id, "paid")
        
        # Add subscription
        user_id = payment['user_id']
        await add_user_subscription(user_id, SUBSCRIPTION_DAYS)
        
        # Notify user (bot is injected in app)
        bot = request.app.get('bot')
        if bot:
            await bot.send_message(
                chat_id=user_id,
                text=f"✅ To'lov qabul qilindi!\n\nSizga {SUBSCRIPTION_DAYS} kunlik obuna taqdim etildi."
            )
            
        return web.Response(status=200, text="Success")
        
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return web.Response(status=500, text="Internal format error")

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

    # Routerlarni ro'yxatdan o'tkazish
    dp.include_router(user_handlers.router)
    dp.include_router(payment_handler.router)  # To'lov tasdiqlash (approve/reject)
    dp.include_router(article_handler.router)
    dp.include_router(assignment_handler.router)
    dp.include_router(ai_chat_handler.router)
    dp.include_router(admin_handler.router)

    # Start simple web server for Render health check
    app = web.Application()
    app['bot'] = bot
    app.router.add_get("/", handle)
    app.router.add_post("/webhook/payment", payment_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    try:
        logging.info(f"Starting web server on port {port}...")
        await site.start()
        
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
