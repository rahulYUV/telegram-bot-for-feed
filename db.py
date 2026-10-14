import aiosqlite

DB_NAME = "instagram_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                chat_id INTEGER,
                instagram_user TEXT,
                PRIMARY KEY (chat_id, instagram_user)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS seen_posts (
                instagram_user TEXT,
                post_id TEXT PRIMARY KEY
            )
        """)
        await db.commit()

async def add_subscription(chat_id: int, username: str) -> bool:
    username = username.lower().lstrip("@")
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                "INSERT INTO subscriptions (chat_id, instagram_user) VALUES (?, ?)",
                (chat_id, username)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

async def remove_subscription(chat_id: int, username: str) -> bool:
    username = username.lower().lstrip("@")
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "DELETE FROM subscriptions WHERE chat_id = ? AND instagram_user = ?",
            (chat_id, username)
        )
        await db.commit()
        return cursor.rowcount > 0

async def get_user_subscriptions(chat_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT instagram_user FROM subscriptions WHERE chat_id = ?",
            (chat_id,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def get_all_active_targets():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT DISTINCT instagram_user, chat_id FROM subscriptions")
        return await cursor.fetchall()

async def is_post_seen(post_id: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT 1 FROM seen_posts WHERE post_id = ?", (post_id,))
        row = await cursor.fetchone()
        return row is not None

async def mark_post_seen(username: str, post_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO seen_posts (instagram_user, post_id) VALUES (?, ?)",
            (username.lower(), post_id)
        )
        await db.commit()