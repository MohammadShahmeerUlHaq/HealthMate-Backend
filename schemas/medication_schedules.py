from pydantic import BaseModel, Field
from typing import Optional
import datetime

class MedicationScheduleCreate(BaseModel):
    time: datetime.time
    dosage_instruction: Optional[str] = Field(None, max_length=200)

class MedicationScheduleUpdate(BaseModel):
    time: Optional[datetime.time] = None
    dosage_instruction: Optional[str] = Field(None, max_length=200)

class MedicationScheduleResponse(BaseModel):
    id: int
    medication_id: int
    time: datetime.time
    dosage_instruction: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
