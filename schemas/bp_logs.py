from datetime import datetime, date,  time
from pydantic import BaseModel, Field
from typing import Optional

class BloodPressureLogBase(BaseModel):
    systolic: int = Field(..., gt=0, lt=300)
    diastolic: int = Field(..., gt=0, lt=200)
    pulse: Optional[int] = Field(None, gt=0, lt=250)
    notes: Optional[str] = Field(None, max_length=500)

class BloodPressureLogCreate(BloodPressureLogBase):
    checked_at: Optional[datetime] = None

class BloodPressureLogUpdate(BloodPressureLogBase):
    checked_at: Optional[datetime] = None

class BPScheduleSchema(BaseModel):
    id: int
    user_id: int
    time: time
    duration_days: int
    start_date: date
    end_date: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class BloodPressureLogOut(BloodPressureLogBase):
    id: int
    schedule: BPScheduleSchema
    checked_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
