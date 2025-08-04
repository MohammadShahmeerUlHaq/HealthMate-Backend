from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db

from models.users import User
from models.medicines import Medicine
from crud.medicines import (
    get_medicine_by_medicine_id,
    get_medicines,
    create_medicine
)
from schemas.medicines import (
    MedicineCreate, MedicineResponse
)
from middlewares.auth import get_current_user

router = APIRouter()

@router.get("", response_model=List[MedicineResponse])
def list_medicines(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """List all medicines. Returns a list"""
    result = get_medicines(db)

    if result is None or (isinstance(result, list) and not result):
        raise HTTPException(status_code=404, detail="Medicine(s) not found.")

    return result


@router.get("/{medicine_id}", response_model=MedicineResponse)
def get_medicine_by_id(medicine_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Get a specific medicine by its ID."""
    medicine = get_medicine_by_medicine_id(db, medicine_id)
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found.")
    return medicine


@router.post("", response_model=MedicineResponse, status_code=201)
def create_new_medicine(payload: MedicineCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Create a new medicine or return an existing one."""
    medicine = create_medicine(db, payload.name, payload.strength)
    db.commit()
    db.refresh(medicine)
    return medicine