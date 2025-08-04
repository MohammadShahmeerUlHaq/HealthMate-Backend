from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta, date, time
from models.medications import Medication
from models.medication_schedules import MedicationSchedule
from models.medicines import Medicine
from .medicines import create_medicine
from sqlalchemy.exc import NoResultFound, IntegrityError
from schemas.medications import MedicationUpdate
from fastapi import HTTPException, status

def create_medication_with_schedules(db: Session, user_id: int, payload) -> Medication:
    """Create medication along with its schedules."""
    # 1️⃣ Get or create medicine
    medicine = create_medicine(db, payload.name, payload.strength)

    # 2️⃣ Compute duration
    duration_days = (payload.end_date - payload.start_date).days + 1
    if duration_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after or equal to start date."
        )

    # 3️⃣ Create medication
    medication = Medication(
        user_id=user_id,
        medicine_id=medicine.id,
        purpose=payload.purpose,
        duration_days=duration_days,
        start_date=payload.start_date,
        end_date=payload.end_date
    )
    db.add(medication)
    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        # Check if it's the unique constraint
        if 'unique_medication' in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medication for this medicine already exists for the user."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while creating medication."
            )

    # 4️⃣ Create schedules
    for schedule_data in payload.schedules:
        schedule = MedicationSchedule(
            medication_id=medication.id,
            time=schedule_data.time,
            dosage_instruction=schedule_data.dosage_instruction
        )
        db.add(schedule)

    return medication


def count_medications(db: Session, user_id: int) -> int:
    return db.query(Medication).filter(
        Medication.user_id == user_id,
        Medication.is_active.is_(True)
    ).count()


def get_user_medicines(db: Session, user_id: int) -> List[Medicine]:
    return (
        db.query(Medicine)
        .join(Medication, Medication.medicine_id == Medicine.id)
        .filter(Medication.user_id == user_id)
        .distinct()
        .all()
    )


def get_user_medications(db: Session, user_id: int) -> List[Medication]:
    """List all medications for a user."""
    return db.query(Medication).filter_by(user_id=user_id).all()

# def normalize_time(t: time) -> time:
#     return t.replace(second=0, microsecond=0)


def normalize_time(t: time) -> time:
    # Remove seconds, microseconds, and tzinfo for consistent comparison
    return t.replace(second=0, microsecond=0, tzinfo=None)

def update_medication(db: Session, medication_id: int, payload: MedicationUpdate) -> Optional[Medication]:
    medication = db.query(Medication).filter_by(id=medication_id).first()
    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found."
        )

    # Validate dates
    duration_days = (payload.end_date - payload.start_date).days + 1
    if duration_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after or equal to start date."
        )

    # Get or create medicine
    medicine = create_medicine(db, payload.name.strip(), payload.strength.strip())

    # Update medication fields
    medication.medicine_id = medicine.id
    medication.purpose = payload.purpose.strip() if payload.purpose else None
    medication.start_date = payload.start_date
    medication.end_date = payload.end_date
    medication.duration_days = duration_days

    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        if 'unique_medication' in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medication for this medicine already exists for the user."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected DB error during medication update."
        )

    # Process schedules
    for sched in payload.schedules:
        norm_time = normalize_time(sched.time)
        instruction = (
            sched.dosage_instruction.strip()
            if sched.dosage_instruction and sched.dosage_instruction.strip()
            else None
        )

        existing = db.query(MedicationSchedule).filter_by(
            medication_id=medication.id,
            time=norm_time
        ).first()

        if not existing:
            # ➕ New time — insert
            db.add(MedicationSchedule(
                medication_id=medication.id,
                time=norm_time,
                dosage_instruction=instruction,
                is_active=True
            ))
        elif not existing.is_active:
            # ✅ Exists but inactive — reactivate and update instruction
            existing.is_active = True
            existing.dosage_instruction = instruction
        elif instruction is not None:
            # ✏️ Exists and active — update instruction only if provided
            existing.dosage_instruction = instruction

    db.flush()
    return medication

# def update_medication(db: Session, medication_id: int, payload: MedicationUpdate) -> Optional[Medication]:
    medication = db.query(Medication).filter_by(id=medication_id).first()
    if not medication:
        return None

    # Update or create medicine
    medicine = create_medicine(db, payload.name.strip(), payload.strength.strip())

    medication.medicine_id = medicine.id
    medication.purpose = payload.purpose.strip()
    medication.start_date = payload.start_date
    medication.end_date = payload.end_date
    medication.duration_days = (payload.end_date - payload.start_date).days + 1

    if medication.duration_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after or equal to start date."
        )

    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        # Check if it's the unique constraint
        if 'unique_medication' in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medication for this medicine already exists for the user."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while creating medication."
            )

    # Map new schedules by time
    new_schedule_map = {sched.time: sched.dosage_instruction.strip() for sched in payload.schedules}

    # Map existing active schedules by time
    existing_active_schedules = {
        sched.time: sched for sched in medication.schedules if sched.is_active
    }

    # 1. Update or create schedules
    for time, new_instruction in new_schedule_map.items():
        if time in existing_active_schedules:
            existing_schedule = existing_active_schedules[time]
            existing_schedule.dosage_instruction = new_instruction  # ✅ Update dosage
        else:
            # ➕ Add new schedule
            new_schedule = MedicationSchedule(
                medication_id=medication.id,
                time=time,
                dosage_instruction=new_instruction,
                is_active=True
            )
            db.add(new_schedule)

    # 2. Deactivate schedules not in new payload
    new_times = set(new_schedule_map.keys())
    for time, sched in existing_active_schedules.items():
        if time not in new_times:
            sched.is_active = False

    db.flush()
    return medication


def delete_medication(db: Session, medication_id: int, user_id: int) -> bool:
    """Delete a medication and its schedules."""
    medication = db.query(Medication).filter_by(id=medication_id, user_id=user_id).first()
    if not medication:
        return False
    db.delete(medication)
    return True


# def update_medication(db: Session, medication_id: int, payload) -> Optional[Medication]:
    """Update an existing medication."""
    medication = db.query(Medication).filter_by(id=medication_id).first()
    if not medication:
        return None
    if payload.purpose is not None:
        medication.purpose = payload.purpose
    if payload.duration_days is not None:
        medication.duration_days = payload.duration_days
        medication.end_date = medication.start_date + timedelta(days=payload.duration_days)
    return medication