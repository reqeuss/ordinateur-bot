import aiosqlite
from pathlib import Path
from config import DB_PATH, STARTING_COOKIES

class Database:
    def __init__(self, path=DB_PATH):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        return aiosqlite.connect(self.path)

    async def init(self):
        async with self.connect() as db:
            await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                cookies INTEGER NOT NULL DEFAULT 250,
                bank INTEGER NOT NULL DEFAULT 0,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 0,
                last_daily INTEGER NOT NULL DEFAULT 0,
                last_work INTEGER NOT NULL DEFAULT 0,
                last_freecoffee INTEGER NOT NULL DEFAULT 0,
                last_rob INTEGER NOT NULL DEFAULT 0,
                last_crime INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                created_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS inventory (
                guild_id INTEGER,
                user_id INTEGER,
                item TEXT,
                amount INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, item)
            );
            CREATE TABLE IF NOT EXISTS settings (
                guild_id INTEGER PRIMARY KEY,
                welcome_channel INTEGER,
                leave_channel INTEGER,
                modlog_channel INTEGER,
                ticket_category INTEGER,
                ticket_panel_channel INTEGER,
                partnership_channel INTEGER,
                rules_channel INTEGER,
                announcements_channel INTEGER,
                giveaway_channel INTEGER
            );
            CREATE TABLE IF NOT EXISTS giveaways (
                message_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                channel_id INTEGER,
                prize TEXT,
                winners INTEGER,
                end_at INTEGER,
                ended INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS tickets (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                owner_id INTEGER,
                created_at INTEGER
            );
            """)
            await db.commit()

    async def ensure_user(self, guild_id, user_id):
        async with self.connect() as db:
            await db.execute(
                "INSERT OR IGNORE INTO users(guild_id,user_id,cookies) VALUES(?,?,?)",
                (guild_id, user_id, STARTING_COOKIES)
            )
            await db.commit()

    async def get_user(self, guild_id, user_id):
        await self.ensure_user(guild_id, user_id)
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM users WHERE guild_id=? AND user_id=?",
                (guild_id, user_id)
            )
            return await cur.fetchone()

    async def change_money(self, guild_id, user_id, amount, bank=False):
        await self.ensure_user(guild_id, user_id)
        field = "bank" if bank else "cookies"
        async with self.connect() as db:
            await db.execute(f"UPDATE users SET {field}={field}+? WHERE guild_id=? AND user_id=?",
                             (amount, guild_id, user_id))
            await db.commit()

    async def set_money(self, guild_id, user_id, amount, bank=False):
        await self.ensure_user(guild_id, user_id)
        field = "bank" if bank else "cookies"
        async with self.connect() as db:
            await db.execute(f"UPDATE users SET {field}=? WHERE guild_id=? AND user_id=?",
                             (max(0, amount), guild_id, user_id))
            await db.commit()

    async def set_timestamp(self, guild_id, user_id, field, value):
        await self.ensure_user(guild_id, user_id)
        allowed = {"last_daily","last_work","last_freecoffee","last_rob","last_crime"}
        if field not in allowed:
            raise ValueError("Champ invalide")
        async with self.connect() as db:
            await db.execute(f"UPDATE users SET {field}=? WHERE guild_id=? AND user_id=?",
                             (value, guild_id, user_id))
            await db.commit()

    async def add_xp(self, guild_id, user_id, amount):
        user = await self.get_user(guild_id, user_id)
        old_level = user["level"]
        xp = user["xp"] + amount
        level = int((xp / 100) ** 0.5)
        async with self.connect() as db:
            await db.execute("UPDATE users SET xp=?,level=? WHERE guild_id=? AND user_id=?",
                             (xp, level, guild_id, user_id))
            await db.commit()
        return old_level, level

    async def leaderboard(self, guild_id, limit=10):
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM users WHERE guild_id=? ORDER BY cookies+bank DESC LIMIT ?",
                (guild_id, limit)
            )
            return await cur.fetchall()

    async def top_level(self, guild_id, limit=10):
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM users WHERE guild_id=? ORDER BY level DESC,xp DESC LIMIT ?",
                (guild_id, limit)
            )
            return await cur.fetchall()

    async def add_item(self, guild_id, user_id, item, amount=1):
        await self.ensure_user(guild_id, user_id)
        async with self.connect() as db:
            await db.execute("""INSERT INTO inventory VALUES(?,?,?,?)
                ON CONFLICT(guild_id,user_id,item) DO UPDATE SET amount=amount+excluded.amount""",
                (guild_id, user_id, item, amount))
            await db.commit()

    async def get_inventory(self, guild_id, user_id):
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT item,amount FROM inventory WHERE guild_id=? AND user_id=? AND amount>0",
                (guild_id,user_id)
            )
            return await cur.fetchall()

    async def remove_item(self, guild_id, user_id, item, amount=1):
        async with self.connect() as db:
            cur = await db.execute(
                "SELECT amount FROM inventory WHERE guild_id=? AND user_id=? AND item=?",
                (guild_id,user_id,item)
            )
            row = await cur.fetchone()
            if not row or row[0] < amount:
                return False
            await db.execute(
                "UPDATE inventory SET amount=amount-? WHERE guild_id=? AND user_id=? AND item=?",
                (amount,guild_id,user_id,item)
            )
            await db.commit()
            return True

    async def add_warning(self, guild_id, user_id, moderator_id, reason, created_at):
        async with self.connect() as db:
            cur = await db.execute(
                "INSERT INTO warnings(guild_id,user_id,moderator_id,reason,created_at) VALUES(?,?,?,?,?)",
                (guild_id,user_id,moderator_id,reason,created_at)
            )
            await db.commit()
            return cur.lastrowid

    async def get_warnings(self, guild_id, user_id):
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM warnings WHERE guild_id=? AND user_id=? ORDER BY id DESC",
                (guild_id,user_id)
            )
            return await cur.fetchall()

    async def clear_warnings(self, guild_id, user_id):
        async with self.connect() as db:
            await db.execute("DELETE FROM warnings WHERE guild_id=? AND user_id=?",
                             (guild_id,user_id))
            await db.commit()

    async def set_setting(self, guild_id, field, value):
        allowed = {
            "welcome_channel","leave_channel","modlog_channel","ticket_category",
            "ticket_panel_channel","partnership_channel","rules_channel",
            "announcements_channel","giveaway_channel"
        }
        if field not in allowed:
            raise ValueError("Paramètre invalide")
        async with self.connect() as db:
            await db.execute(f"""INSERT INTO settings(guild_id,{field}) VALUES(?,?)
                ON CONFLICT(guild_id) DO UPDATE SET {field}=excluded.{field}""",
                (guild_id,value))
            await db.commit()

    async def get_settings(self, guild_id):
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM settings WHERE guild_id=?", (guild_id,))
            return await cur.fetchone()

    async def save_giveaway(self, data):
        async with self.connect() as db:
            await db.execute("""INSERT OR REPLACE INTO giveaways
                (message_id,guild_id,channel_id,prize,winners,end_at,ended)
                VALUES(?,?,?,?,?,?,?)""", data)
            await db.commit()

    async def active_giveaways(self):
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM giveaways WHERE ended=0")
            return await cur.fetchall()

    async def end_giveaway(self, message_id):
        async with self.connect() as db:
            await db.execute("UPDATE giveaways SET ended=1 WHERE message_id=?", (message_id,))
            await db.commit()

    async def save_ticket(self, channel_id, guild_id, owner_id, created_at):
        async with self.connect() as db:
            await db.execute("INSERT OR REPLACE INTO tickets VALUES(?,?,?,?)",
                             (channel_id,guild_id,owner_id,created_at))
            await db.commit()

    async def ticket_by_owner(self, guild_id, owner_id):
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM tickets WHERE guild_id=? AND owner_id=?",
                                   (guild_id,owner_id))
            return await cur.fetchone()

    async def delete_ticket(self, channel_id):
        async with self.connect() as db:
            await db.execute("DELETE FROM tickets WHERE channel_id=?", (channel_id,))
            await db.commit()
