import aiosqlite
from datetime import datetime

DB_PATH = "decoys.db"

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
        await db.commit()

async def find_customer(decoy_email):
    async with aiosqlite.connect("decoys.db") as db:
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
    # Placeholder — later: insert into log table or file
