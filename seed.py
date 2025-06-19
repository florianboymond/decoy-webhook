import asyncio
from db import insert_decoy

async def seed():
    await insert_decoy(
        "john@acumenpulse.com",
        "microfarmcolorado@gmail.com",
        "Leak Alert from Email Decoys"
    )

asyncio.run(seed())
