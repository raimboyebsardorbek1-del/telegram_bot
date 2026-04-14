import hashlib
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from cachetools import TTLCache

# We use a simple TTL cache to keep track of requests per user ID
# 1-second TTL means 1 message per second allowed per user
rate_limit_cache = TTLCache(maxsize=10000, ttl=1)

def hash_password(password: str) -> str:
    """Returns SHA-256 hash of a given password."""
    return hashlib.sha256(password.encode()).hexdigest()

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
