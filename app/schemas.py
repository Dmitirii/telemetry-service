from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

class UserCreate(BaseModel):
    name: str

class UserResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class DeviceCreate(BaseModel):
    name: str

class DeviceResponse(BaseModel):
    id: int
    user_id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class StatCreate(BaseModel):
    x: float
    y: float
    z: float
    timestamp: Optional[datetime] = None

class StatResponse(BaseModel):
    id: int
    device_id: int
    timestamp: datetime
    x: float
    y: float
    z: float

    class Config:
        from_attributes = True

from typing import Optional

class StatsAnalysis(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    count: int
    sum: float
    median: Optional[float] = None

class DeviceStatsResponse(BaseModel):
    device_id: int
    period: Dict[str, str]
    x: StatsAnalysis
    y: StatsAnalysis
    z: StatsAnalysis