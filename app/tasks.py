from celery import shared_task
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime
from app.models import Device, Stat, User
from app.crud import median
import os
import asyncio
from collections import defaultdict

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./telemetry.db")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@shared_task(bind=True)
def compute_device_stats(self, device_id: int, start: str, end: str):
    async def _run():
        async for db in get_db():
            result = await db.execute(select(Device).where(Device.id == device_id))
            if not result.scalar_one_or_none():
                return {"error": "Device not found"}
            result = await db.execute(
                select(Stat.x, Stat.y, Stat.z)
                .where(Stat.device_id == device_id, Stat.timestamp.between(start, end))
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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_run())

@shared_task(bind=True)
def compute_user_stats(self, user_id: int, start: str, end: str):
    async def _run():
        async for db in get_db():
            result = await db.execute(select(User).where(User.id == user_id))
            if not result.scalar_one_or_none():
                return {"error": "User not found"}
            result_dev = await db.execute(select(Device.id).where(Device.user_id == user_id))
            device_ids = [row[0] for row in result_dev.all()]
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
                select(Stat.device_id, Stat.x, Stat.y, Stat.z)
                .where(Stat.device_id.in_(device_ids), Stat.timestamp.between(start, end))
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
                    median_val = (sorted_vals[mid-1] + sorted_vals[mid]) / 2
                else:
                    median_val = sorted_vals[mid]
                return {"min": mn, "max": mx, "count": n, "sum": s, "median": median_val}
            per_device = {}
            all_x, all_y, all_z = [], [], []
            for dev_id, points in device_data.items():
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                zs = [p[2] for p in points]
                per_device[str(dev_id)] = {
                    "device_id": dev_id,
                    "period": {"start": start, "end": end},
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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_run())