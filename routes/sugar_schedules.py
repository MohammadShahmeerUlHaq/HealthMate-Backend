from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from middlewares.auth import get_current_user
from schemas.sugar_schedules import (
    SugarScheduleCreate, SugarScheduleUpdate, SugarScheduleResponse
)
from crud.sugar_schedules import (
    get_user_sugar_schedules, create_sugar_schedule, update_sugar_schedule, delete_sugar_schedule
)
from models.users import User
from models.sugar_schedules import SugarSchedule
router = APIRouter()

@router.get("", response_model=List[SugarScheduleResponse])
def list_sugar_schedules(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_user_sugar_schedules(db, current_user.id)

@router.post("", response_model=List[SugarScheduleResponse], status_code=201)
def create_schedule(payload: SugarScheduleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    schedule = create_sugar_schedule(db, current_user.id, payload)
    # db.commit()
    # db.refresh(schedule)
    return schedule

@router.put("/{schedule_id}", response_model=SugarScheduleResponse)
def update_schedule(schedule_id: int, payload: SugarScheduleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    schedule = update_sugar_schedule(db, schedule_id, payload)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.commit()
    db.refresh(schedule)
    return schedule

@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = delete_sugar_schedule(db, schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.commit()
    return