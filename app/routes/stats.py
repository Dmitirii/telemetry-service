from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app import crud, schemas
from app.database import get_db
from celery.result import AsyncResult
from app.celery_app import celery_app
from app.tasks import compute_device_stats, compute_user_stats

router = APIRouter(prefix="/devices", tags=["stats"])

# Синхронные эндпоинты (существующие)
@router.post("/{device_id}/stats/", response_model=schemas.StatResponse)
async def add_stat(device_id: int, stat: schemas.StatCreate, db: AsyncSession = Depends(get_db)):
    device = await crud.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return await crud.add_stat(db, device_id, stat)

@router.get("/{device_id}/stats/", response_model=schemas.DeviceStatsResponse)
async def get_device_stats(
    device_id: int,
    start: datetime = Query(..., description="Начало периода"),
    end: datetime = Query(..., description="Конец периода"),
    db: AsyncSession = Depends(get_db)
):
    device = await crud.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    stats = await crud.get_device_stats(db, device_id, start, end)
    return schemas.DeviceStatsResponse(
        device_id=device_id,
        period={"start": start.isoformat(), "end": end.isoformat()},
        x=schemas.StatsAnalysis(**stats["x"]),
        y=schemas.StatsAnalysis(**stats["y"]),
        z=schemas.StatsAnalysis(**stats["z"])
    )

# Асинхронные эндпоинты (Celery)
@router.post("/{device_id}/stats/async/")
async def device_stats_async(
    device_id: int,
    start: datetime = Query(...),
    end: datetime = Query(...),
):
    """Запуск фонового вычисления статистики по устройству"""
    task = compute_device_stats.delay(device_id, start.isoformat(), end.isoformat())
    return {"task_id": task.id, "status": "Processing"}

@router.post("/users/{user_id}/stats/async/")
async def user_stats_async(
    user_id: int,
    start: datetime = Query(...),
    end: datetime = Query(...),
):
    """Запуск фонового вычисления статистики по пользователю"""
    task = compute_user_stats.delay(user_id, start.isoformat(), end.isoformat())
    return {"task_id": task.id, "status": "Processing"}

@router.get("/tasks/{task_id}/")
async def get_task_result(task_id: str):
    """Получение результата фоновой задачи"""
    task = AsyncResult(task_id, app=celery_app)
    if task.ready():
        return {"task_id": task_id, "status": "completed", "result": task.result}
    else:
        return {"task_id": task_id, "status": "pending"}