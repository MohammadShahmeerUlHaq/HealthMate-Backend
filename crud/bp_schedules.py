from sqlalchemy.orm import Session
from datetime import timedelta, date
from models.bp_schedules import BloodPressureSchedule
from typing import List, Optional
from schemas.bp_schedules import BPScheduleCreate, BPScheduleUpdate, BPScheduleResponse
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

def get_user_bp_schedules(db: Session, user_id: int) -> List[BloodPressureSchedule]:
    return db.query(BloodPressureSchedule).filter_by(user_id=user_id).all()

def create_bp_schedule(db: Session, user_id: int, payload: BPScheduleCreate) -> List[BloodPressureSchedule]:
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
        schedule = BloodPressureSchedule(
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

# def create_bp_schedule(db: Session, user_id: int, payload: BPScheduleCreate ) -> BloodPressureSchedule:
#     if not payload.start_date:
#         start_date = date.today()
#     end_date = payload.end_date
#     duration_days = (payload.end_date - payload.start_date).days + 1
#     if duration_days <= 0:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="End date must be after or equal to start date."
#         )
#     schedule = BloodPressureSchedule(
#         user_id=user_id,
#         time=payload.time,
#         duration_days=duration_days,
#         start_date=start_date,
#         end_date=end_date
#     )
#     db.add(schedule)
#     db.flush()
#     return schedule

def update_bp_schedule(db: Session, schedule_id: int, payload: BPScheduleUpdate) -> Optional[BloodPressureSchedule]:
    # try:
        schedule = db.query(BloodPressureSchedule).filter_by(id=schedule_id).first()

        if not schedule:
            raise HTTPException(status_code=404, detail="Blood Pressure Schedule not found")

        # Cache original dates for validation and duration update
        original_start = schedule.start_date
        original_end = schedule.end_date

        if payload.start_date is not None and payload.end_date is not None:
            if payload.end_date < payload.start_date:
                raise HTTPException(status_code=400, detail="end_date cannot be before start_date")
            schedule.start_date = payload.start_date
            schedule.end_date = payload.end_date

        # Handle start_date
        elif payload.start_date is not None:
            if schedule.end_date and payload.start_date > schedule.end_date:
                raise HTTPException(status_code=400, detail="start_date cannot be after end_date")
            schedule.start_date = payload.start_date

        # Handle end_date
        elif payload.end_date is not None:
            if payload.end_date < (payload.start_date or schedule.start_date):
                raise HTTPException(status_code=400, detail="end_date cannot be before start_date")
            schedule.end_date = payload.end_date

        # Handle duration_days if dates changed        
        if payload.start_date is not None or payload.end_date is not None:
            start = payload.start_date or schedule.start_date
            end = payload.end_date or schedule.end_date
            schedule.duration_days = (end - start).days + 1

        # Handle time
        if payload.time is not None:
            schedule.time = payload.time

        # Handle is_active
        if payload.is_active is not None:
            schedule.is_active = payload.is_active

        db.commit()
        db.refresh(schedule)
        return schedule

    # except SQLAlchemyError as e:
    #     db.rollback()
    #     raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def delete_bp_schedule(db: Session, schedule_id: int) -> bool:
    schedule = db.query(BloodPressureSchedule).filter_by(id=schedule_id).first()
    if not schedule:
        return False
    db.delete(schedule)
    return True
