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

async def click_webhook(request):
    """
    Handles Click.uz Merchant API webhooks (Prepare and Complete).
    """
    try:
        data = await request.post()
        logging.info(f"Click Webhook Data: {dict(data)}")
        
        click_trans_id = data.get("click_trans_id")
        service_id = data.get("service_id")
        click_paydoc_id = data.get("click_paydoc_id")
        merchant_trans_id = data.get("merchant_trans_id") # This is our Order ID
        amount = data.get("amount")
        action = data.get("action")
        error = data.get("error")
        sign_time = data.get("sign_time")
        sign_string = data.get("sign_string")
        
        # 1. Verify Signature
        from services.click_service import verify_click_signature
        if not verify_click_signature(click_trans_id, service_id, click_paydoc_id, merchant_trans_id, amount, action, error, sign_time, sign_string):
            return web.json_response({"error": -1, "error_note": "SIGN CHECK FAILED!"})
            
        # 2. Check Order in DB
        order = await get_order(merchant_trans_id)
        if not order:
            return web.json_response({"error": -5, "error_note": "ORDER NOT FOUND!"})
            
        # 3. Check Amount (optional but recommended)
        if float(amount) < order['amount']:
             return web.json_response({"error": -2, "error_note": "INCORRECT AMOUNT!"})

        # 4. Handle Prepare Action
        if action == '0':
            if order['status'] != 'pending':
                return web.json_response({"error": -4, "error_note": "ALREADY PAID OR CANCELLED"})
            
            return web.json_response({
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": merchant_trans_id,
                "error": 0,
                "error_note": "Success"
            })

        # 5. Handle Complete Action
        elif action == '1':
            if error != '0':
                return web.json_response({"error": error, "error_note": "CLICK ERROR"})
            
            if order['status'] == 'paid':
                return web.json_response({"error": -4, "error_note": "ALREADY PAID"})

            # Mark as paid
            await update_order_status(merchant_trans_id, "paid")
            
            # Fulfill Order (Generate AI content)
            bot = request.app.get('bot')
            from services.generation_service import fulfill_order
            asyncio.create_task(fulfill_order(bot, order))
            
            return web.json_response({
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": merchant_trans_id,
                "error": 0,
                "error_note": "Success"
            })

        return web.json_response({"error": -3, "error_note": "ACTION NOT SUPPORTED"})
        
    except Exception as e:
        logging.error(f"Click Webhook Error: {e}")
        return web.json_response({"error": -9, "error_note": "INTERNAL SERVER ERROR"})

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
    app.router.add_post("/webhook/click", click_webhook)
    
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
