import aiosqlite
import logging

logger = logging.getLogger(__name__)
DB = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                name TEXT,
                lang TEXT DEFAULT 'ru',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS ratelimit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER NOT NULL,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_history_tg ON history(tg_id);
            CREATE INDEX IF NOT EXISTS idx_rl_tg ON ratelimit(tg_id);
        """)
        await db.commit()
    logger.info("БД инициализирована")


async def ensure_user(tg_id, username=None, name=None, lang="ru"):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (tg_id, username, name, lang) VALUES (?,?,?,?)",
            (tg_id, username, name, lang)
        )
        await db.commit()


async def get_history(tg_id: int, limit: int = 20):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT role, content FROM history WHERE tg_id=? ORDER BY created_at DESC LIMIT ?",
            (tg_id, limit)
        )
        rows = await cur.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


async def add_message(tg_id: int, role: str, content: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO history (tg_id, role, content) VALUES (?,?,?)",
            (tg_id, role, content)
        )
        await db.commit()


async def clear_history(tg_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM history WHERE tg_id=?", (tg_id,))
        await db.commit()


async def check_ratelimit(tg_id: int, max_rpm: int) -> bool:
    """Возвращает True если можно делать запрос."""
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM ratelimit WHERE tg_id=? AND ts > datetime('now','-1 minute')",
            (tg_id,)
        )
        row = await cur.fetchone()
        count = row[0]
        if count >= max_rpm:
            return False
        await db.execute("INSERT INTO ratelimit (tg_id) VALUES (?)", (tg_id,))
        await db.execute("DELETE FROM ratelimit WHERE ts < datetime('now','-1 hour')")
        await db.commit()
        return True
