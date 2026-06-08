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
                parameters TEXT,
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

        # Referrals Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                referrer_id INTEGER,
                referred_id INTEGER UNIQUE,
                ordered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Run migrations for usage table to add esse_used and kurs_used
        async with db.execute("PRAGMA table_info(usage)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
        if "esse_used" not in columns:
            await db.execute("ALTER TABLE usage ADD COLUMN esse_used INTEGER DEFAULT 0")
        if "kurs_used" not in columns:
            await db.execute("ALTER TABLE usage ADD COLUMN kurs_used INTEGER DEFAULT 0")

        await db.commit()
        logging.info("Database initialized with all tables and migrations applied.")

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

async def ban_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def unban_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
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

async def create_order(order_id: str, user_id: int, service_type: str, pages: str, amount: float, parameters: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO orders (order_id, user_id, service_type, pages, amount, parameters) VALUES (?, ?, ?, ?, ?, ?)",
            (order_id, user_id, service_type, pages, amount, parameters)
        )
        await db.commit()

async def get_order(order_id: str) -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT order_id, user_id, service_type, pages, amount, status, parameters FROM orders WHERE order_id = ?",
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
                    "status": row[5],
                    "parameters": row[6]
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

# --- REFERRAL FUNCTIONS ---
async def add_referral(referrer_id: int, referred_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO referrals (referrer_id, referred_id, ordered) VALUES (?, ?, 0)",
            (referrer_id, referred_id)
        )
        await db.commit()

async def get_referrer(referred_id: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT referrer_id FROM referrals WHERE referred_id = ?", (referred_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_referral_stats(user_id: int) -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,)) as cursor:
            total_referred = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND ordered = 1", (user_id,)) as cursor:
            ordered_referred = (await cursor.fetchone())[0]
        # 3000 for each registration, and another 3000 for each that ordered
        total_bonus = (total_referred * 3000) + (ordered_referred * 3000)
        return {
            "total_referred": total_referred,
            "ordered_referred": ordered_referred,
            "total_bonus": total_bonus
        }

async def mark_referral_order_completed(referred_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE referrals SET ordered = 1 WHERE referred_id = ?", (referred_id,))
        await db.commit()

async def has_referred_ordered(referred_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT ordered FROM referrals WHERE referred_id = ?", (referred_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] == 1 if row else False

# --- ADMIN STATS ---
async def get_stats() -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid'") as c2:
            paid_orders = (await c2.fetchone())[0]
        return {"users": total_users, "paid_orders": paid_orders}

async def get_detailed_admin_stats() -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]
        
        async with db.execute("SELECT COUNT(*) FROM orders") as c:
            total_orders = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid'") as c:
            paid_orders = (await c.fetchone())[0]
            
        async with db.execute("SELECT SUM(amount) FROM orders WHERE status = 'paid' AND date(created_at) = date('now')") as c:
            daily_rev = (await c.fetchone())[0] or 0.0
            
        async with db.execute("SELECT SUM(amount) FROM orders WHERE status = 'paid' AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')") as c:
            monthly_rev = (await c.fetchone())[0] or 0.0

        async with db.execute("SELECT SUM(amount) FROM orders WHERE status = 'paid'") as c:
            total_rev = (await c.fetchone())[0] or 0.0

        async with db.execute("""
            SELECT u.id, u.name, u.username, COUNT(o.order_id) as order_count 
            FROM users u 
            JOIN orders o ON u.id = o.user_id 
            WHERE o.status = 'paid' 
            GROUP BY u.id 
            ORDER BY order_count DESC 
            LIMIT 5
        """) as c:
            active_users = await c.fetchall()

        async with db.execute("SELECT COUNT(*) FROM referrals") as c:
            total_referrals = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM referrals WHERE ordered = 1") as c:
            ordered_referrals = (await c.fetchone())[0]

        return {
            "total_users": total_users,
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "daily_revenue": daily_rev,
            "monthly_revenue": monthly_rev,
            "total_revenue": total_rev,
            "active_users": active_users,
            "total_referrals": total_referrals,
            "ordered_referrals": ordered_referrals
        }
