from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from middlewares.auth import get_current_user
from database import get_db
from schemas.bp_logs import (
    BloodPressureLogCreate,
    BloodPressureLogUpdate,
    BloodPressureLogOut,
)
from crud.bp_logs import (
    get_active_schedule,
    create_bp_log,
    update_bp_log,
    delete_bp_log,
    get_log_by_id,
    get_logs_by_schedule_id,
    get_logs_by_user_id,
    get_logs_by_date_range,
    get_logs_by_date
)
from models.users import User

router = APIRouter()


@router.post("/{schedule_id}", response_model=BloodPressureLogOut, status_code=status.HTTP_201_CREATED)
def create_log(schedule_id: int, data: BloodPressureLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = create_bp_log(db, user_id=current_user.id, schedule_id=schedule_id, data=data)
    if not log:
        raise HTTPException(status_code=400, detail="No active schedule found for the provided time.")
    return log


@router.put("/logs/{log_id}", response_model=BloodPressureLogOut)
def update_log(log_id: int, data: BloodPressureLogUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = update_bp_log(db, log_id, data)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found.")
    return log


@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log(log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not delete_bp_log(db, log_id):
        raise HTTPException(status_code=404, detail="Log not found.")
    return


@router.get("/logs/{log_id}", response_model=BloodPressureLogOut)
def get_log_by_id(log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = get_log_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found.")
    return log


@router.get("/schedule/{schedule_id}", response_model=List[BloodPressureLogOut])
def get_logs_by_schedule(schedule_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_logs_by_schedule_id(db, schedule_id)


@router.get("/user", response_model=List[BloodPressureLogOut])
def get_logs_by_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_logs_by_user_id(db, current_user.id)


@router.get("/date", response_model=List[BloodPressureLogOut])
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
