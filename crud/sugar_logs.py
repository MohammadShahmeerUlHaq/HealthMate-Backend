from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import datetime, date

from models.sugar_logs import SugarLog
from models.sugar_schedules import SugarSchedule
from schemas.sugar_logs import SugarLogCreate, SugarLogUpdate

def create_sugar_log(db: Session, user_id: int, schedule_id: int, data: SugarLogCreate) -> SugarLog:
    if schedule_id:
        schedule = db.query(SugarSchedule).filter_by(id=schedule_id, user_id=user_id).first()
        if not schedule:
            raise PermissionError("Invalid schedule ID or not authorized")

    log = SugarLog(
        value=data.value,
        type=data.type,
        notes=data.notes,
        checked_at=data.checked_at or datetime.utcnow(),
        schedule_id=schedule_id,
    )
    # infer user_id from schedule
    log.schedule = db.query(SugarSchedule).filter_by(id=schedule_id).first() if schedule_id else None
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_sugar_log_by_id(db: Session, log_id: int, user_id: int) -> Optional[SugarLog]:
    return db.query(SugarLog).join(SugarSchedule).filter(
        SugarLog.id == log_id,
        SugarSchedule.user_id == user_id
    ).first()

def get_sugar_logs_by_schedule(db: Session, schedule_id: int, user_id: int) -> List[SugarLog]:
    return db.query(SugarLog).join(SugarSchedule).filter(
        SugarLog.schedule_id == schedule_id,
        SugarSchedule.user_id == user_id
    ).all()

def get_sugar_logs_by_user(db: Session, user_id: int) -> List[SugarLog]:
    return db.query(SugarLog).join(SugarSchedule).filter(SugarSchedule.user_id == user_id).all()

def get_recent_sugar_logs(db: Session, user_id: int, limit: int = 4) -> List[SugarLog]:
    return (
        db.query(SugarLog)
        .join(SugarSchedule)
        .filter(SugarSchedule.user_id == user_id)
        .order_by(SugarLog.checked_at.desc())
        .limit(limit)
        .all()
    )

def get_sugar_logs_by_date_range(db: Session, user_id: int, start: date, end: date) -> List[SugarLog]:
    return db.query(SugarLog).join(SugarSchedule).filter(
        SugarSchedule.user_id == user_id,
        SugarLog.checked_at >= datetime.combine(start, datetime.min.time()),
        SugarLog.checked_at <= datetime.combine(end, datetime.max.time())
    ).all()

def get_sugar_logs_by_date(db: Session, user_id: int, target_date: date) -> List[SugarLog]:
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())

    return db.query(SugarLog).join(SugarSchedule).filter(
        SugarSchedule.user_id == user_id,
        SugarLog.checked_at >= start_dt,
        SugarLog.checked_at <= end_dt
    ).all()

def update_sugar_log(db: Session, log_id: int, user_id: int, data: SugarLogUpdate) -> Optional[SugarLog]:
    log = db.query(SugarLog).join(SugarSchedule).filter(
        SugarLog.id == log_id,
        SugarSchedule.user_id == user_id
    ).first()

    if not log:
        return None

    update_data = data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(log, key, value)

    db.commit()
    db.refresh(log)
    return log

def delete_sugar_log(db: Session, log_id: int, user_id: int) -> bool:
    log = db.query(SugarLog).join(SugarSchedule).filter(
        SugarLog.id == log_id,
        SugarSchedule.user_id == user_id
    ).first()

    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
