from pydantic import BaseModel, Field
from datetime import datetime, date, time
from typing import Optional
from enum import Enum
from models.sugar_logs import SugarType

class SugarLogBase(BaseModel):
    value: float = Field(..., gt=0, lt=1000)
    type: SugarType
    notes: Optional[str] = None
    checked_at: Optional[datetime] = None

class SugarLogCreate(SugarLogBase):
    pass

class SugarLogUpdate(BaseModel):
    value: Optional[float] = Field(None, gt=0, lt=1000)
    type: Optional[SugarType] = None
    notes: Optional[str] = None
    checked_at: Optional[datetime] = None

class SugarScheduleSchema(BaseModel):
    id: int
    user_id: int
    time: time
    duration_days: int
    start_date: date
    end_date: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class SugarLogOut(SugarLogBase):
    id: int
    created_at: datetime
    schedule: SugarScheduleSchema

    class Config:
        from_attributes = True
