from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_user(db, user)

@router.post("/{user_id}/devices/", response_model=schemas.DeviceResponse)
async def create_device(user_id: int, device: schemas.DeviceCreate, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await crud.create_device(db, user_id, device)

@router.get("/{user_id}/stats/")
async def get_user_stats(
    user_id: int,
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    stats = await crud.get_user_stats(db, user_id, start, end)
    return {
        "user_id": user_id,
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "total": stats["total"],
        "per_device": stats["per_device"]
    }