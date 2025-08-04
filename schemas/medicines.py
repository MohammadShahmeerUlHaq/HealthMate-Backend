from pydantic import BaseModel, Field
from typing import Optional

class MedicineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    strength: str = Field(..., min_length=1, max_length=50)


class MedicineResponse(BaseModel):
    id: int
    name: str
    strength: str

    class Config:
        from_attributes = True