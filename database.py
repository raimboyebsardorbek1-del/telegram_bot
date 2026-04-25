import aiosqlite
import logging

DB_NAME = "bot_database.sqlite"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Users Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_end TIMESTAMP DEFAULT NULL
            )
        ''')
        
        # Banned Users
        await db.execute('''
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY
            )
        ''')

        # AI History
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ai_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Usage Tracking (Free Once)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS usage (
                user_id INTEGER PRIMARY KEY,
                maqola_used INTEGER DEFAULT 0,
                mustaqil_used INTEGER DEFAULT 0,
                referat_used INTEGER DEFAULT 0,
                taqdimot_used INTEGER DEFAULT 0
            )
        ''')

        # Orders Table (Pay Per Order)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER,
                service_type TEXT,
                pages TEXT,
                amount REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Balances Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS balances (
                user_id INTEGER PRIMARY KEY,
                amount REAL DEFAULT 0
            )
        ''')

        await db.commit()
        logging.info("Database initialized with all tables.")

# --- USER FUNCTIONS ---
async def add_user(user_id: int, name: str, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (id, name, username) VALUES (?, ?, ?)",
            (user_id, name, username)
        )
        # Initialize usage and balance
        await db.execute("INSERT OR IGNORE INTO usage (user_id) VALUES (?)", (user_id,))
        await db.execute("INSERT OR IGNORE INTO balances (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def is_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None

async def log_ai_history(user_id: int, message: str, response: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO ai_history (user_id, message, response) VALUES (?, ?, ?)",
            (user_id, message, response)
        )
        await db.commit()

async def get_user_chat_history(user_id: int, limit: int = 5) -> list[tuple]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT message, response FROM ai_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return rows[::-1]

# --- USAGE & ORDER FUNCTIONS ---
async def check_free_usage(user_id: int, service_type: str) -> bool:
    """Returns True if free usage is available for the given service."""
    column = f"{service_type.lower()}_used"
    async with aiosqlite.connect(DB_NAME) as db:
        # Ensure user exists in usage table
        await db.execute("INSERT OR IGNORE INTO usage (user_id) VALUES (?)", (user_id,))
        async with db.execute(f"SELECT {column} FROM usage WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] == 0 if row else True

async def mark_free_usage(user_id: int, service_type: str):
    column = f"{service_type.lower()}_used"
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f"UPDATE usage SET {column} = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def create_order(order_id: str, user_id: int, service_type: str, pages: str, amount: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO orders (order_id, user_id, service_type, pages, amount) VALUES (?, ?, ?, ?, ?)",
            (order_id, user_id, service_type, pages, amount)
        )
        await db.commit()

async def get_order(order_id: str) -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT order_id, user_id, service_type, pages, amount, status FROM orders WHERE order_id = ?",
            (order_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "order_id": row[0],
                    "user_id": row[1],
                    "service_type": row[2],
                    "pages": row[3],
                    "amount": row[4],
                    "status": row[5]
                }
            return None

async def update_order_status(order_id: str, status: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        await db.commit()

# --- BALANCE FUNCTIONS ---
async def get_balance(user_id: int) -> float:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT amount FROM balances WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0.0

async def update_balance(user_id: int, amount: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO balances (user_id) VALUES (?)", (user_id,))
        await db.execute("UPDATE balances SET amount = amount + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

# --- ADMIN STATS ---
async def get_stats() -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid'") as c2:
            paid_orders = (await c2.fetchone())[0]
        return {"users": total_users, "paid_orders": paid_orders}
