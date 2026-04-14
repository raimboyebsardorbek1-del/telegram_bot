import logging
from aiogram import Bot
from database import get_all_users

async def broadcast_message(bot: Bot, text: str) -> tuple[int, int]:
    """
    Sends a broadcast message to all users in the database safely.
    Returns a tuple containing (success_count, fail_count).
    """
    users = await get_all_users()
    success = 0
    fail = 0
    
    for user_id in users:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            success += 1
        except Exception as e:
            logging.error(f"Failed to send broadcast to user_id {user_id}: {e}")
            fail += 1
            
    return success, fail
