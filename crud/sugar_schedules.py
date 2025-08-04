from sqlalchemy.orm import Session
from datetime import timedelta, date
from models.sugar_schedules import SugarSchedule
from schemas.sugar_schedules import SugarScheduleCreate
from typing import List, Optional
from fastapi import HTTPException, status

def get_user_sugar_schedules(db: Session, user_id: int) -> List[SugarSchedule]:
    return db.query(SugarSchedule).filter_by(user_id=user_id).all()

# def create_sugar_schedule(db: Session, user_id: int, time, duration_days: int, start_date) -> SugarSchedule:
#     if not start_date:
#         from datetime import date
#         start_date = date.today()
#     end_date = start_date + timedelta(days=duration_days)
#     schedule = SugarSchedule(
#         user_id=user_id,
#         time=time,
#         duration_days=duration_days,
#         start_date=start_date,
#         end_date=end_date
#     )
#     db.add(schedule)
#     db.flush()
#     return schedule

def create_sugar_schedule(db: Session, user_id: int, payload: SugarScheduleCreate) -> List[SugarSchedule]:
    start_date = payload.start_date or date.today()
    end_date = payload.end_date

    if not end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date is required."
        )

    duration_days = (end_date - start_date).days + 1
    if duration_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after or equal to start date."
        )

    schedules = []
    for t in payload.times:
        schedule = SugarSchedule(
            user_id=user_id,
            time=t,
            duration_days=duration_days,
            start_date=start_date,
            end_date=end_date
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        schedules.append(schedule)

    db.flush()  # Use flush to assign IDs before returning
    return schedules

def update_sugar_schedule(db: Session, schedule_id: int, payload) -> Optional[SugarSchedule]:
    schedule = db.query(SugarSchedule).filter_by(id=schedule_id).first()
    if not schedule:
        return None
    if payload.time:
        schedule.time = payload.time
    start_date = schedule.start_date
    end_date = schedule.end_date
    if payload.start_date:
        start_date = payload.start_date
    if payload.end_date:
        end_date = payload.end_date

    duration_days = (end_date - start_date).days + 1
    if duration_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after or equal to start date."
        )
    schedule.start_date = start_date
    schedule.end_date = end_date
    schedule.duration_days = duration_days
    
    if payload.is_active is not None:
        schedule.is_active = payload.is_active
    return schedule

def delete_sugar_schedule(db: Session, schedule_id: int) -> bool:
    schedule = db.query(SugarSchedule).filter_by(id=schedule_id).first()
    if not schedule:
        return False
    db.delete(schedule)
    return True
