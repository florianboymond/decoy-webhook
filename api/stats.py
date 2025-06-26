from fastapi import APIRouter, Depends
import aiosqlite
from config import config
from auth import get_current_user

router = APIRouter()

@router.get("/api/stats")
async def get_stats(current_user: str = Depends(get_current_user)):
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        # Get total decoys
        async with db.execute("SELECT COUNT(*) FROM decoys") as cursor:
            total_decoys = (await cursor.fetchone())[0]
        
        # Get alerts triggered (events count)
        async with db.execute("SELECT COUNT(*) FROM events") as cursor:
            alerts_triggered = (await cursor.fetchone())[0]
        
        # Get unique use cases as industries (simplified)
        async with db.execute("SELECT DISTINCT use_case FROM decoys WHERE use_case IS NOT NULL") as cursor:
            industries = [row[0] for row in await cursor.fetchall()]
        
        # For now, return placeholder data for titles and locations
        # These would need additional fields in the database
        titles = ["CEO", "VP Sales", "Legal Counsel"]
        locations = ["San Francisco", "New York", "Remote"]
        
        return {
            "total_decoys": total_decoys,
            "alerts_triggered": alerts_triggered,
            "industries": industries,
            "titles": titles,
            "locations": locations
        }