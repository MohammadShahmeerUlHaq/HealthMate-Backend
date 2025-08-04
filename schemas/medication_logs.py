from pydantic import BaseModel
from datetime import datetime, date, time
from typing import Optional

# Nested schemas

class MedicineSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class MedicationSchema(BaseModel):
    id: int
    medicine: MedicineSchema

    class Config:
        from_attributes = True

class MedicationScheduleSchema(BaseModel):
    id: int
    time: time
    dosage_instruction: Optional[str]
    medication: MedicationSchema

    class Config:
        from_attributes = True

# Base schemas

class MedicationLogBase(BaseModel):
    scheduled_date: date
    taken_at: Optional[datetime] = None
    notes: Optional[str] = None

class MedicationLogCreate(MedicationLogBase):
    pass

class MedicationLogUpdate(BaseModel):
    taken_at: Optional[datetime] = None
    notes: Optional[str] = None

class MedicationLogResponse(MedicationLogBase):
    id: int
    created_at: datetime
    updated_at: datetime
    medication_schedule: MedicationScheduleSchema

    class Config:
        from_attributes = True
