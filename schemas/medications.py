from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from datetime import datetime, time, date

class MedicationScheduleCreate(BaseModel):
    time: time
    dosage_instruction: Optional[str] = Field(None, min_length=1, max_length=200)

class MedicationCreateWithSchedules(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    strength: str = Field(..., min_length=1, max_length=50)
    purpose: Optional[str] = Field(None, max_length=500)
    start_date: date
    end_date: date
    schedules: List[MedicationScheduleCreate]

    @model_validator(mode='before')
    def validate_dates(cls, values):
        start = values.get("start_date")
        end = values.get("end_date")
        if start and end and end < start:
            raise ValueError("End date must be greater than or equal to start date")
        return values

class MedicationUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    strength: str = Field(..., min_length=1, max_length=50)
    purpose: Optional[str] = Field(None, max_length=500)
    start_date: date
    end_date: date
    schedules: List[MedicationScheduleCreate]

    @model_validator(mode='before')
    def validate_dates(cls, values):
        start = values.get("start_date")
        end = values.get("end_date")
        if start and end and end < start:
            raise ValueError("End date must be greater than or equal to start date")
        return values


class MedicationScheduleResponse(BaseModel):
    id: int
    time: time
    dosage_instruction: Optional[str]

    class Config:
        from_attributes = True


class MedicineResponse(BaseModel):
    id: int
    name: str
    strength: str

    class Config:
        from_attributes = True


class MedicationResponse(BaseModel):
    id: int
    user_id: int
    medicine: MedicineResponse
    purpose: Optional[str]
    duration_days: int
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    schedules: List[MedicationScheduleResponse]

    class Config:
        from_attributes = True