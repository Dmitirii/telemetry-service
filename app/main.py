from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db
from app.routes import users, stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Telemetry Service", lifespan=lifespan)

app.include_router(users.router)
app.include_router(stats.router)

@app.get("/")
async def root():
    return {"message": "Telemetry Service is running"}