from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from middlewares.auth import get_current_user
from models.medication_schedules import MedicationSchedule
from models.medications import Medication
from models.users import User
from crud.medication_schedules import (
    get_schedules_for_medication,
    create_medication_schedule,
    update_medication_schedule,
    delete_medication_schedule
)
from schemas.medication_schedules import (
    MedicationScheduleCreate,
    MedicationScheduleUpdate,
    MedicationScheduleResponse
)

router = APIRouter()


@router.get("/medications/{medication_id}/schedules", response_model=List[MedicationScheduleResponse])
def list_schedules_for_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all schedules for a specific medication belonging to the current user."""
    medication = db.query(Medication).filter_by(id=medication_id, user_id=current_user.id).first()
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found.")
    return get_schedules_for_medication(db, medication_id)

@router.get("", response_model=List[MedicationScheduleResponse])
def list_schedules_for_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schedules = (
        db.query(MedicationSchedule)
        .join(Medication)
        .filter(Medication.user_id == current_user.id)
        .all()
    )
    return schedules


@router.post("/medications/{medication_id}/schedules", response_model=MedicationScheduleResponse, status_code=201)
def create_new_schedule(
    medication_id: int,
    payload: MedicationScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new schedule to a medication."""
    medication = db.query(Medication).filter_by(id=medication_id, user_id=current_user.id).first()
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found.")
    schedule_exists = db.query(MedicationSchedule).filter_by(
        medication_id=medication_id, time=payload.time, is_active=True
    ).first()
    if schedule_exists:
        raise HTTPException(status_code=400, detail="Schedule already present.")
    schedule = create_medication_schedule(db, medication_id, payload.time, payload.dosage_instruction)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.put("/{schedule_id}", response_model=MedicationScheduleResponse)
def update_schedule(
    schedule_id: int,
    payload: MedicationScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing medication schedule."""
    schedule = db.query(MedicationSchedule).filter_by(id=schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    medication = db.query(Medication).filter_by(id=schedule.medication_id, user_id=current_user.id).first()
    if not medication:
        raise HTTPException(status_code=404, detail="You do not have permission to update this schedule.")
    update_medication_schedule(db, schedule_id, payload)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an existing medication schedule."""
    schedule = db.query(MedicationSchedule).filter_by(id=schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    medication = db.query(Medication).filter_by(id=schedule.medication_id, user_id=current_user.id).first()
    if not medication:
        raise HTTPException(status_code=404, detail="You do not have permission to delete this schedule.")
    delete_medication_schedule(db, schedule_id)
    db.commit()
    return
