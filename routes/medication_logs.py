from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas.medication_logs import (
    MedicationLogCreate,
    MedicationLogUpdate,
    MedicationLogResponse
)
from crud.medication_logs import (
    create_log,
    get_log_if_owned,
    get_logs_by_schedule_id,
    update_log,
    delete_log,
    get_logs_by_date,
    get_logs_by_date_range,
    get_logs_by_medicine,
    get_logs_by_user
)
from typing import List, Optional
from models import User
from middlewares.auth import get_current_user
from datetime import date

router = APIRouter()

@router.get("/logs/user", response_model=List[MedicationLogResponse])
def list_user_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_logs_by_user(db, current_user.id)


@router.post("/{schedule_id}", response_model=MedicationLogResponse, status_code=status.HTTP_201_CREATED)
def create_medication_log(
    schedule_id: int,
    payload: MedicationLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_log(db, schedule_id, payload, current_user.id)

@router.get("/{log_id}", response_model=MedicationLogResponse)
def get_medication_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_log_if_owned(db, log_id, current_user.id)

@router.get("/schedule/{schedule_id}", response_model=List[MedicationLogResponse])
def get_logs_by_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_logs_by_schedule_id(db, schedule_id, current_user.id)

@router.put("/{log_id}", response_model=MedicationLogResponse)
def update_medication_log(
    log_id: int,
    payload: MedicationLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_log(db, log_id, payload, current_user.id)

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    delete_log(db, log_id, current_user.id)

@router.get("", response_model=List[MedicationLogResponse])
def get_logs_by_date_or_range(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if date_from and date_to:
        logs = get_logs_by_date_range(db, current_user.id, date_from, date_to)
    elif date_from:
        logs = get_logs_by_date(db, current_user.id, date_from)
    else:
        raise HTTPException(status_code=400, detail="Please provide at least date_from or both date_from and date_to")

    return logs

@router.get("/medicine/{medicine_id}", response_model=List[MedicationLogResponse])
def _get_logs_by_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_logs_by_medicine(db, current_user.id, medicine_id)
