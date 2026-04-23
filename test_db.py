import asyncio
from app.database import init_db

asyncio.run(init_db())
print("База данных создана (telemetry.db)")
