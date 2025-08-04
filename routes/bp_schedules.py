from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from middlewares.auth import get_current_user
from schemas.bp_schedules import BPScheduleCreate, BPScheduleUpdate, BPScheduleResponse
from crud.bp_schedules import (
    get_user_bp_schedules,
    create_bp_schedule,
    update_bp_schedule,
    delete_bp_schedule
)
from models.bp_schedules import BloodPressureSchedule
from models.users import User

router = APIRouter()

@router.get("", response_model=List[BPScheduleResponse])
def list_bp_schedules(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_user_bp_schedules(db, current_user.id)

@router.post("", response_model=List[BPScheduleResponse], status_code=201)
def create_schedule(payload: BPScheduleCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    schedule = create_bp_schedule(db, current_user.id, payload)
    # db.commit()
    # db.refresh(schedule)
    return schedule

@router.put("/{schedule_id}", response_model=BPScheduleResponse)
def update_schedule(schedule_id: int, payload: BPScheduleUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    schedule = update_bp_schedule(db, schedule_id, payload)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.commit()
    db.refresh(schedule)
    return schedule

@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    success = delete_bp_schedule(db, schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.commit()
    return