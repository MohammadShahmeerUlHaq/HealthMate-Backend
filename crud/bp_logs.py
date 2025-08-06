from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date

from models.bp_logs import BloodPressureLog
from models.bp_schedules import BloodPressureSchedule
from schemas.bp_logs import BloodPressureLogCreate, BloodPressureLogUpdate

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

def get_active_schedule(db: Session, user_id: int, checked_date: date) -> Optional[BloodPressureSchedule]:
    return db.query(BloodPressureSchedule).filter(
        BloodPressureSchedule.user_id == user_id,
        BloodPressureSchedule.is_active == True,
        BloodPressureSchedule.start_date <= checked_date,
        (BloodPressureSchedule.end_date == None) | (BloodPressureSchedule.end_date >= checked_date)
    ).first()


def create_bp_log(db: Session, user_id: int, schedule_id: int, data: BloodPressureLogCreate) -> Optional[BloodPressureLog]:
    checked_at = data.checked_at or datetime.utcnow()
    checked_date = checked_at.date()

    schedule = db.query(BloodPressureSchedule).filter(
        BloodPressureSchedule.id == schedule_id,
        BloodPressureSchedule.user_id == user_id
    ).first()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found for this user."
        )

    log = BloodPressureLog(
        schedule_id=schedule.id,
        systolic=data.systolic,
        diastolic=data.diastolic,
        pulse=data.pulse,
        notes=data.notes,
        checked_at=checked_at
    )

    try:
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    except IntegrityError as e:
        db.rollback()

        # You can inspect the error string to give more specific messages
        error_message = str(e.orig)

        if "check_systolic_range" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Systolic must be between 1 and 299 and greater than diastolic."
            )
        elif "check_diastolic_range" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Diastolic must be between 1 and 199 and less than systolic."
            )
        elif "check_pulse_range" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pulse must be NULL or between 1 and 249."
            )
        elif "check_systolic_greater_than_diastolic" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Systolic must be greater than diastolic."
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid blood pressure log data. Please check your input."
        )


def update_bp_log(db: Session, log_id: int, data: BloodPressureLogUpdate) -> Optional[BloodPressureLog]:
    log = db.query(BloodPressureLog).filter(BloodPressureLog.id == log_id).first()
    if not log:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_bp_log(db: Session, log_id: int) -> bool:
    log = db.query(BloodPressureLog).filter(BloodPressureLog.id == log_id).first()
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True


def get_log_by_id(db: Session, log_id: int) -> Optional[BloodPressureLog]:
    return db.query(BloodPressureLog).filter(BloodPressureLog.id == log_id).first()


def get_logs_by_schedule_id(db: Session, schedule_id: int) -> List[BloodPressureLog]:
    return db.query(BloodPressureLog).filter(BloodPressureLog.schedule_id == schedule_id).order_by(BloodPressureLog.checked_at.desc()).all()


def get_logs_by_user_id(db: Session, user_id: int) -> List[BloodPressureLog]:
    return db.query(BloodPressureLog).join(BloodPressureSchedule).filter(
        BloodPressureSchedule.user_id == user_id
    ).order_by(BloodPressureLog.checked_at.desc()).all()

def get_recent_bp_logs(db: Session, user_id: int, limit: int = 4) -> List[BloodPressureLog]:
    return (
        db.query(BloodPressureLog)
        .join(BloodPressureSchedule)
        .filter(BloodPressureSchedule.user_id == user_id)
        .order_by(BloodPressureLog.checked_at.desc())
        .limit(limit)
        .all()
    )

def get_logs_by_date_range(db: Session, user_id: int, start_date: date, end_date: date) -> List[BloodPressureLog]:
    # Convert date objects to datetime objects to cover the full day range
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    
    return db.query(BloodPressureLog).join(BloodPressureSchedule).filter(
        BloodPressureSchedule.user_id == user_id,
        BloodPressureLog.checked_at >= start_dt,
        BloodPressureLog.checked_at <= end_dt
    ).order_by(BloodPressureLog.checked_at.desc()).all()


def get_logs_by_date(db: Session, user_id: int, target_date: date) -> List[BloodPressureLog]:
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())

    return db.query(BloodPressureLog).join(BloodPressureSchedule).filter(
        BloodPressureSchedule.user_id == user_id,
        BloodPressureLog.checked_at >= start_dt,
        BloodPressureLog.checked_at <= end_dt
    ).order_by(BloodPressureLog.checked_at.desc()).all()


# from sqlalchemy.orm import Session
# from typing import Optional, List
# from datetime import datetime, date

# from models.bp_logs import BloodPressureLog
# from models.bp_schedules import BloodPressureSchedule
# from schemas.bp_logs import BloodPressureLogCreate, BloodPressureLogUpdate

# from sqlalchemy.exc import IntegrityError
# from fastapi import HTTPException, status

# def get_active_schedule(db: Session, user_id: int, checked_date: date) -> Optional[BloodPressureSchedule]:
#     return db.query(BloodPressureSchedule).filter(
#         BloodPressureSchedule.user_id == user_id,
#         BloodPressureSchedule.is_active == True,
#         BloodPressureSchedule.start_date <= checked_date,
#         (BloodPressureSchedule.end_date == None) | (BloodPressureSchedule.end_date >= checked_date)
#     ).first()


# def create_bp_log(db: Session, user_id: int, schedule_id: int, data: BloodPressureLogCreate) -> Optional[BloodPressureLog]:
#     checked_at = data.checked_at or datetime.utcnow()
#     checked_date = checked_at.date()

#     schedule = db.query(BloodPressureSchedule).filter(
#         BloodPressureSchedule.id == schedule_id,
#         BloodPressureSchedule.user_id == user_id
#     ).first()

#     if not schedule:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Schedule not found for this user."
#         )

#     log = BloodPressureLog(
#         schedule_id=schedule.id,
#         systolic=data.systolic,
#         diastolic=data.diastolic,
#         pulse=data.pulse,
#         notes=data.notes,
#         checked_at=checked_at
#     )

#     try:
#         db.add(log)
#         db.commit()
#         db.refresh(log)
#         return log
#     except IntegrityError as e:
#         db.rollback()

#         # You can inspect the error string to give more specific messages
#         error_message = str(e.orig)

#         if "check_systolic_range" in error_message:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Systolic must be between 1 and 299 and greater than diastolic."
#             )
#         elif "check_diastolic_range" in error_message:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Diastolic must be between 1 and 199 and less than systolic."
#             )
#         elif "check_pulse_range" in error_message:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Pulse must be NULL or between 1 and 249."
#             )
#         elif "check_systolic_greater_than_diastolic" in error_message:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Systolic must be greater than diastolic."
#             )

#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid blood pressure log data. Please check your input."
#         )


# # def create_bp_log(db: Session, user_id: int, schedule_id: int, data: BloodPressureLogCreate) -> Optional[BloodPressureLog]:
#     checked_at = data.checked_at or datetime.utcnow()
#     checked_date = checked_at.date()
#     # schedule = get_active_schedule(db, user_id, checked_at.date())
#     schedule = db.query(BloodPressureSchedule).filter(
#         BloodPressureSchedule.id == schedule_id
#         # BloodPressureSchedule.is_active == True,
#         # BloodPressureSchedule.start_date <= checked_date,
#         # (BloodPressureSchedule.end_date == None) | (BloodPressureSchedule.end_date >= checked_date)
#     ).first()

#     if not schedule:
#         return None

#     log = BloodPressureLog(
#         schedule_id=schedule.id,
#         systolic=data.systolic,
#         diastolic=data.diastolic,
#         pulse=data.pulse,
#         notes=data.notes,
#         checked_at=checked_at
#     )
#     db.add(log)
#     db.commit()
#     db.refresh(log)
#     return log


# def update_bp_log(db: Session, log_id: int, data: BloodPressureLogUpdate) -> Optional[BloodPressureLog]:
#     log = db.query(BloodPressureLog).filter(BloodPressureLog.id == log_id).first()
#     if not log:
#         return None

#     for field, value in data.dict(exclude_unset=True).items():
#         setattr(log, field, value)

#     db.commit()
#     db.refresh(log)
#     return log


# def delete_bp_log(db: Session, log_id: int) -> bool:
#     log = db.query(BloodPressureLog).filter(BloodPressureLog.id == log_id).first()
#     if not log:
#         return False

#     db.delete(log)
#     db.commit()
#     return True


# def get_log_by_id(db: Session, log_id: int) -> Optional[BloodPressureLog]:
#     return db.query(BloodPressureLog).filter(BloodPressureLog.id == log_id).first()


# def get_logs_by_schedule_id(db: Session, schedule_id: int) -> List[BloodPressureLog]:
#     return db.query(BloodPressureLog).filter(BloodPressureLog.schedule_id == schedule_id).order_by(BloodPressureLog.checked_at.desc()).all()


# def get_logs_by_user_id(db: Session, user_id: int) -> List[BloodPressureLog]:
#     return db.query(BloodPressureLog).join(BloodPressureSchedule).filter(
#         BloodPressureSchedule.user_id == user_id
#     ).order_by(BloodPressureLog.checked_at.desc()).all()

# def get_recent_bp_logs(db: Session, user_id: int, limit: int = 4) -> List[BloodPressureLog]:
#     return (
#         db.query(BloodPressureLog)
#         .join(BloodPressureSchedule)
#         .filter(BloodPressureSchedule.user_id == user_id)
#         .order_by(BloodPressureLog.checked_at.desc())
#         .limit(limit)
#         .all()
#     )

# def get_logs_by_date_range(db: Session, user_id: int, start: datetime, end: datetime) -> List[BloodPressureLog]:
#     return db.query(BloodPressureLog).join(BloodPressureSchedule).filter(
#         BloodPressureSchedule.user_id == user_id,
#         BloodPressureLog.checked_at >= start,
#         BloodPressureLog.checked_at <= end
#     ).order_by(BloodPressureLog.checked_at.desc()).all()


# def get_logs_by_date(db: Session, user_id: int, target_date: date) -> List[BloodPressureLog]:
#     start_dt = datetime.combine(target_date, datetime.min.time())
#     end_dt = datetime.combine(target_date, datetime.max.time())

#     return db.query(BloodPressureLog).join(BloodPressureSchedule).filter(
#         BloodPressureSchedule.user_id == user_id,
#         BloodPressureLog.checked_at >= start_dt,
#         BloodPressureLog.checked_at <= end_dt
#     ).order_by(BloodPressureLog.checked_at.desc()).all()
