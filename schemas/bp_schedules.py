from pydantic import BaseModel, Field
# from datetime import time, date, datetime
import datetime
from typing import Optional, List

class BPScheduleCreate(BaseModel):
    times: List[datetime.time]
    start_date: Optional[datetime.date]
    end_date: datetime.date

class BPScheduleUpdate(BaseModel):
    time: Optional[datetime.time] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    is_active: Optional[bool] = None

# print(BPScheduleUpdate.model_json_schema())

class BPScheduleResponse(BaseModel):
    id: int
    user_id: int
    time: datetime.time
    duration_days: int
    start_date: datetime.date
    end_date: Optional[datetime.date]
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True