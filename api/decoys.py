from fastapi import APIRouter, Depends
import aiosqlite
from config import config
from auth import get_current_user

router = APIRouter()

@router.get("/api/decoys")
async def get_decoys(current_user: str = Depends(get_current_user)):
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        # Get decoys with alert counts
        query = """
        SELECT 
            d.decoy_email,
            d.use_case,
            d.created_at,
            COUNT(e.id) as alerts
        FROM decoys d
        LEFT JOIN events e ON d.decoy_email = e.decoy_email
        GROUP BY d.decoy_email, d.use_case, d.created_at
        ORDER BY d.created_at DESC
        """
        
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            
            decoys = []
            for row in rows:
                decoys.append({
                    "decoy_email": row[0],
                    "use_case": row[1],
                    "created_at": row[2][:10] if row[2] else None,  # Format as YYYY-MM-DD
                    "alerts": row[3]
                })
            
            return decoys