from sqlalchemy.orm import Session, joinedload
from models import MedicationLog, MedicationSchedule, Medication
from schemas.medication_logs import MedicationLogCreate, MedicationLogUpdate
from fastapi import HTTPException
from datetime import date
from typing import List
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

def create_log(db: Session, schedule_id: int, log_data, user_id: int):
    schedule = (
        db.query(MedicationSchedule)
        .options(joinedload(MedicationSchedule.medication))
        .filter(MedicationSchedule.id == schedule_id)
        .first()
    )

    if not schedule or schedule.medication.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to create log for this medication")
    
    # log_data.medication_schedule_id = schedule_id
    log = MedicationLog(medication_schedule_id=schedule_id, **log_data.model_dump())
    db.add(log)
    try:
        db.commit()
        db.refresh(log)
        return log
    except IntegrityError as e:
        db.rollback()
        if 'medication_schedule_id' in str(e.orig) and 'scheduled_date' in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A log for this schedule and date already exists.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create medication log due to a database constraint.",
        )
    # db.commit()
    # db.refresh(log)
    # return log

def get_log_if_owned(db: Session, log_id: int, user_id: int):
    log = (
        db.query(MedicationLog)
        .options(
            joinedload(MedicationLog.medication_schedule)
            .joinedload(MedicationSchedule.medication)
            .joinedload(Medication.medicine)
        )
        .filter(MedicationLog.id == log_id)
        .first()
    )

    if not log or log.medication_schedule.medication.user_id != user_id:
        raise HTTPException(status_code=404, detail="Log not found or unauthorized")

    return log

def get_logs_by_schedule_id(db: Session, schedule_id: int, user_id: int) -> List[MedicationLog]:
    return (
        db.query(MedicationLog)
        .join(MedicationLog.medication_schedule)
        .join(MedicationSchedule.medication)
        .filter(
            MedicationSchedule.id == schedule_id,
            MedicationSchedule.medication.has(user_id=user_id)
        )
        .options(
            joinedload(MedicationLog.medication_schedule)
            .joinedload(MedicationSchedule.medication)
            .joinedload(Medication.medicine)  # <--- fixed here
        )
        .all()
    )

def update_log(db: Session, log_id: int, updates: MedicationLogUpdate, user_id: int):
    log = get_log_if_owned(db, log_id, user_id)
    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(log, key, value)

    db.commit()
    db.refresh(log)
    return log

def delete_log(db: Session, log_id: int, user_id: int):
    log = get_log_if_owned(db, log_id, user_id)
    db.delete(log)
    db.commit()
    return True

def get_logs_by_date(db: Session, user_id: int, target_date: date):
    return (
        db.query(MedicationLog)
        .join(MedicationLog.medication_schedule)
        .join(MedicationSchedule.medication)
        .filter(
            MedicationLog.scheduled_date == target_date,
            MedicationSchedule.medication.has(user_id=user_id)
        )
        .options(
            joinedload(MedicationLog.medication_schedule)
            .joinedload(MedicationSchedule.medication)
            .joinedload(Medication.medicine)
        )
        .all()
    )

def get_logs_by_date_range(db: Session, user_id: int, start_date: date, end_date: date):
    return (
        db.query(MedicationLog)
        .join(MedicationLog.medication_schedule)
        .join(MedicationSchedule.medication)
        .filter(
            MedicationLog.scheduled_date.between(start_date, end_date),
            MedicationSchedule.medication.has(user_id=user_id)
        )
        .options(
            joinedload(MedicationLog.medication_schedule)
            .joinedload(MedicationSchedule.medication)
            .joinedload(Medication.medicine)
        )
        .all()
    )

def get_logs_by_medicine(db: Session, user_id: int, medicine_id: int):
    return (
        db.query(MedicationLog)
        .join(MedicationLog.medication_schedule)
        .join(MedicationSchedule.medication)
        .filter(
            MedicationSchedule.medication.has(user_id=user_id, medicine_id=medicine_id)
        )
        .options(
            joinedload(MedicationLog.medication_schedule)
            .joinedload(MedicationSchedule.medication)
            .joinedload(Medication.medicine)
        )
        .all()
    )

def get_logs_by_user(db: Session, user_id: int):
    return (
        db.query(MedicationLog)
        .join(MedicationLog.medication_schedule)
        .join(MedicationSchedule.medication)
        .filter(Medication.user_id == user_id)
        .options(
            joinedload(MedicationLog.medication_schedule)
            .joinedload(MedicationSchedule.medication)
            .joinedload(Medication.medicine)
        )
        .all()
    )