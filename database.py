import aiosqlite
import logging

DB_NAME = "bot_database.sqlite"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_end TIMESTAMP DEFAULT NULL
            )
        ''')
        
        # In case the table already exists but without 'subscription_end'
        try:
            await db.execute("ALTER TABLE users ADD COLUMN subscription_end TIMESTAMP DEFAULT NULL")
        except Exception:
            pass # Column already exists or other error

        await db.execute('''
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ai_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                user_id INTEGER,
                amount REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()
        logging.info("Database initialized with structured tables.")

async def add_user(user_id: int, name: str, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (id, name, username) VALUES (?, ?, ?)",
            (user_id, name, username)
        )
        await db.commit()

async def is_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None

async def ban_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def unban_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        await db.commit()

async def log_ai_history(user_id: int, message: str, response: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO ai_history (user_id, message, response) VALUES (?, ?, ?)",
            (user_id, message, response)
        )
        await db.commit()

async def get_all_users() -> list[int]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_all_users_details() -> list[tuple]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, name, username FROM users") as cursor:
            return await cursor.fetchall()

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM ai_history") as c2:
            total_requests = (await c2.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM banned_users") as c3:
            total_banned = (await c3.fetchone())[0]
        return {"users": total_users, "requests": total_requests, "banned": total_banned}

async def get_user_chat_history(user_id: int, limit: int = 5) -> list[tuple]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT message, response FROM ai_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            # Reverse to give chronological order
            return rows[::-1]

# --- SUBSCRIPTION & PAYMENT FUNCTIONS ---

async def create_payment(payment_id: str, user_id: int, amount: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO payments (payment_id, user_id, amount) VALUES (?, ?, ?)",
            (payment_id, user_id, amount)
        )
        await db.commit()

async def get_payment(payment_id: str) -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT payment_id, user_id, amount, status, created_at FROM payments WHERE payment_id = ?", (payment_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "payment_id": row[0],
                    "user_id": row[1],
                    "amount": row[2],
                    "status": row[3],
                    "created_at": row[4]
                }
            return None

async def update_payment_status(payment_id: str, status: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE payments SET status = ? WHERE payment_id = ?", (status, payment_id))
        await db.commit()

async def add_user_subscription(user_id: int, days: int):
    async with aiosqlite.connect(DB_NAME) as db:
        # Check current subscription
        async with db.execute("SELECT subscription_end FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            
            # Using SQLite date/time modifiers
            if row and row[0]:
                # Add days to existing end date if it's in the future, else from NOW
                # We'll do a simple raw SQL approach
                await db.execute(
                    "UPDATE users SET subscription_end = CASE "
                    "WHEN subscription_end > CURRENT_TIMESTAMP THEN datetime(subscription_end, '+' || ? || ' days') "
                    "ELSE datetime('now', '+' || ? || ' days') END WHERE id = ?",
                    (days, days, user_id)
                )
            else:
                await db.execute("UPDATE users SET subscription_end = datetime('now', '+' || ? || ' days') WHERE id = ?", (days, user_id))
            
        await db.commit()

async def check_subscription(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT 1 FROM users WHERE id = ? AND subscription_end IS NOT NULL AND subscription_end > CURRENT_TIMESTAMP",
            (user_id,)
        ) as cursor:
            return await cursor.fetchone() is not None

async def get_recent_payments(limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT payment_id, user_id, amount, status, created_at FROM payments ORDER BY created_at DESC LIMIT ?", (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [{"payment_id": r[0], "user_id": r[1], "amount": r[2], "status": r[3], "date": r[4]} for r in rows]

