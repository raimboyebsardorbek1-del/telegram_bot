import hashlib
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from cachetools import TTLCache
import os
import time
from docx import Document

# We use a simple TTL cache to keep track of requests per user ID
# 1-second TTL means 1 message per second allowed per user
rate_limit_cache = TTLCache(maxsize=10000, ttl=1)

def hash_password(password: str) -> str:
    """Returns SHA-256 hash of a given password."""
    return hashlib.sha256(password.encode()).hexdigest()

async def send_split_message(message: Message, text: str):
    """Splits a long message into chunks and sends them sequentially."""
    limit = 4000  # Telegram limit is 4096, using 4000 for safety
    if len(text) <= limit:
        await message.answer(text)
    else:
        for i in range(0, len(text), limit):
            chunk = text[i:i + limit]
            await message.answer(chunk)

def cleanup_old_files():
    """Deletes files older than 24 hours from the exports directory."""
    exports_dir = "exports"
    if not os.path.exists(exports_dir):
        return
    
    now = time.time()
    for f in os.listdir(exports_dir):
        f_path = os.path.join(exports_dir, f)
        if os.path.isfile(f_path):
            # 86400 seconds = 24 hours
            if os.stat(f_path).st_mtime < now - 86400:
                try:
                    os.remove(f_path)
                except Exception:
                    pass

def create_docx(text: str, filename: str) -> str:
    """Generates a .docx file from text and returns its path."""
    exports_dir = "exports"
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)
    
    # Run cleanup before creating new ones
    cleanup_old_files()
    
    doc = Document()
    # Simple line-by-line formatting
    for line in text.split('\n'):
        doc.add_paragraph(line)
            
    file_path = os.path.abspath(os.path.join(exports_dir, filename))
    doc.save(file_path)
    return file_path

class ThrottlingMiddleware(BaseMiddleware):
    """Simple anti-spam middleware to prevent rapid messaging (Rate Limit)."""
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user:
            user_id = event.from_user.id
            if user_id in rate_limit_cache:
                # Silently drop the spamming message
                return
            rate_limit_cache[user_id] = True
        return await handler(event, data)

class BannedUserMiddleware(BaseMiddleware):
    """Middleware to check if the user is banned from using the bot."""
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        from database import is_banned
        if event.from_user:
            if await is_banned(event.from_user.id):
                # Optionally inform the user they are banned, or just drop
                return
        return await handler(event, data)
