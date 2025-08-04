from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from middlewares.auth import get_current_user
from crud.medications import (
    create_medication_with_schedules,
    get_user_medications,
    update_medication,
    delete_medication,
    count_medications
)
from schemas.medications import (
    MedicationCreateWithSchedules,
    MedicationResponse,
    MedicationUpdate
)
from models.users import User

router = APIRouter()


@router.post("", response_model=MedicationResponse, status_code=201)
def create_new_medication(payload: MedicationCreateWithSchedules, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new medication along with its schedules for the current user."""
    medication = create_medication_with_schedules(db, current_user.id, payload)
    db.commit()
    db.refresh(medication)
    return medication
    # {
    #     "id": medication.id,
    #     "user_id": medication.user_id,
    #     "medicine_name": medication.medicine.name,
    #     "medicine_strength": medication.medicine.strength,
    #     "purpose": medication.purpose,
    #     "duration_days": medication.duration_days,
    #     "start_date": medication.start_date,
    #     "end_date": medication.end_date,
    #     "created_at": medication.created_at,
    #     "updated_at": medication.updated_at,
    # }


@router.get("/count", response_model=Dict[str, int])
def count_user_medications(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Count active medications for the current user."""
    active_count = count_medications(db, current_user.id)
    return {"active_count": active_count}


@router.get("", response_model=List[MedicationResponse])
def list_user_medications(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """List all medications for the current user."""
    medications = get_user_medications(db, current_user.id)
    return medications
    # [
    #     {
    #         "id": m.id,
    #         "user_id": m.user_id,
    #         "medicine_name": m.medicine.name,
    #         "medicine_strength": m.medicine.strength,
    #         "purpose": m.purpose,
    #         "duration_days": m.duration_days,
    #         "start_date": m.start_date,
    #         "end_date": m.end_date,
    #         "created_at": m.created_at,
    #         "updated_at": m.updated_at,
    #     }
    #     for m in medications
    # ]


@router.put("/{medication_id}", response_model=MedicationResponse)
def update_user_medication(medication_id: int, payload: MedicationUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Update an existing medication."""
    medication = update_medication(db, medication_id, payload)
    if not medication or medication.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Medication not found.")
    db.commit()
    db.refresh(medication)
    return medication
    # {
    #     "id": medication.id,
    #     "user_id": medication.user_id,
    #     "medicine_name": medication.medicine.name,
    #     "medicine_strength": medication.medicine.strength,
    #     "purpose": medication.purpose,
    #     "duration_days": medication.duration_days,
    #     "start_date": medication.start_date,
    #     "end_date": medication.end_date,
    #     "created_at": medication.created_at,
    #     "updated_at": medication.updated_at,
    # }


@router.delete("/{medication_id}", status_code=204)
def delete_user_medication(medication_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete an existing medication."""
    deleted = delete_medication(db, medication_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Medication not found.")
    db.commit()
    return