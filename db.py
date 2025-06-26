import aiosqlite
from datetime import datetime
from config import config

DB_PATH = config.DATABASE_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS decoys (
                decoy_email TEXT PRIMARY KEY,
                customer_email TEXT,
                use_case TEXT,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decoy_email TEXT,
                sender_email TEXT,
                sender_ip TEXT,
                subject TEXT,
                created_at TEXT,
                FOREIGN KEY (decoy_email) REFERENCES decoys (decoy_email)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS authorized_users (
                email TEXT PRIMARY KEY
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS otps (
                email TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used BOOLEAN DEFAULT FALSE
            )
        """)
        await db.commit()

async def find_customer(decoy_email):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT customer_email, use_case FROM decoys WHERE decoy_email = ?", (decoy_email,)) as cursor:
            return await cursor.fetchone()

async def insert_decoy(decoy_email, customer_email, use_case):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO decoys (decoy_email, customer_email, use_case, created_at)
            VALUES (?, ?, ?, ?)
        """, (decoy_email, customer_email, use_case, datetime.utcnow().isoformat()))
        await db.commit()

async def log_event(recipient, sender, ip, subject):
    print(f"LOG → {recipient} hit by {sender} from {ip} with subject '{subject}'")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO events (decoy_email, sender_email, sender_ip, subject, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (recipient, sender, ip, subject, datetime.utcnow().isoformat()))
        await db.commit()
