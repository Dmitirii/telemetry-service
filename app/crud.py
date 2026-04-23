from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app import models, schemas

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    db_user = models.User(name=user.name)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalar_one_or_none()

async def create_device(db: AsyncSession, user_id: int, device: schemas.DeviceCreate):
    db_device = models.Device(user_id=user_id, name=device.name)
    db.add(db_device)
    await db.commit()
    await db.refresh(db_device)
    return db_device

async def get_device(db: AsyncSession, device_id: int):
    result = await db.execute(select(models.Device).where(models.Device.id == device_id))
    return result.scalar_one_or_none()

async def add_stat(db: AsyncSession, device_id: int, stat: schemas.StatCreate):
    db_stat = models.Stat(
        device_id=device_id,
        x=stat.x,
        y=stat.y,
        z=stat.z,
        timestamp=stat.timestamp or datetime.utcnow()
    )
    db.add(db_stat)
    await db.commit()
    await db.refresh(db_stat)
    return db_stat

def median(values):
    n = len(values)
    if n == 0:
        return None
    sorted_vals = sorted(values)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid-1] + sorted_vals[mid]) / 2
    else:
        return sorted_vals[mid]

async def get_device_stats(db: AsyncSession, device_id: int, start: datetime, end: datetime):
    result = await db.execute(
        select(models.Stat.x, models.Stat.y, models.Stat.z)
        .where(models.Stat.device_id == device_id, models.Stat.timestamp.between(start, end))
    )
    rows = result.all()
    if not rows:
        return {
            "x": {"min": None, "max": None, "count": 0, "sum": 0, "median": None},
            "y": {"min": None, "max": None, "count": 0, "sum": 0, "median": None},
            "z": {"min": None, "max": None, "count": 0, "sum": 0, "median": None},
        }
    xs = [r.x for r in rows]
    ys = [r.y for r in rows]
    zs = [r.z for r in rows]
    return {
        "x": {"min": min(xs), "max": max(xs), "count": len(xs), "sum": sum(xs), "median": median(xs)},
        "y": {"min": min(ys), "max": max(ys), "count": len(ys), "sum": sum(ys), "median": median(ys)},
        "z": {"min": min(zs), "max": max(zs), "count": len(zs), "sum": sum(zs), "median": median(zs)},
    }

async def get_user_stats(db: AsyncSession, user_id: int, start: datetime, end: datetime):
    from collections import defaultdict
    result_devices = await db.execute(
        select(models.Device.id).where(models.Device.user_id == user_id)
    )
    device_ids = [row[0] for row in result_devices.all()]
    if not device_ids:
        return {
            "total": {
                "x": {"min": None, "max": None, "count": 0, "sum": 0, "median": None},
                "y": {"min": None, "max": None, "count": 0, "sum": 0, "median": None},
                "z": {"min": None, "max": None, "count": 0, "sum": 0, "median": None}
            },
            "per_device": {}
        }
    result_stats = await db.execute(
        select(models.Stat.device_id, models.Stat.x, models.Stat.y, models.Stat.z)
        .where(models.Stat.device_id.in_(device_ids), models.Stat.timestamp.between(start, end))
    )
    rows = result_stats.all()
    device_data = defaultdict(list)
    for row in rows:
        device_data[row.device_id].append((row.x, row.y, row.z))
    def compute_stats(values):
        if not values:
            return {"min": None, "max": None, "count": 0, "sum": 0, "median": None}
        n = len(values)
        s = sum(values)
        mn = min(values)
        mx = max(values)
        sorted_vals = sorted(values)
        mid = n // 2
        if n % 2 == 0:
            median = (sorted_vals[mid-1] + sorted_vals[mid]) / 2
        else:
            median = sorted_vals[mid]
        return {"min": mn, "max": mx, "count": n, "sum": s, "median": median}
    per_device = {}
    all_x, all_y, all_z = [], [], []
    for dev_id, points in device_data.items():
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        zs = [p[2] for p in points]
        per_device[dev_id] = {
            "device_id": dev_id,
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "x": compute_stats(xs),
            "y": compute_stats(ys),
            "z": compute_stats(zs)
        }
        all_x.extend(xs)
        all_y.extend(ys)
        all_z.extend(zs)
    total = {
        "x": compute_stats(all_x),
        "y": compute_stats(all_y),
        "z": compute_stats(all_z)
    }
    return {"total": total, "per_device": per_device}