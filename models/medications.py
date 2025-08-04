import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, 
    Enum, Text, Float, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base

class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False, index=True)

    purpose = Column(String(500), nullable=True)  # Why this medication is prescribed
    duration_days = Column(Integer, nullable=False)
    start_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)  # Calculated field: start_date + duration_days
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="medications")
    medicine = relationship("Medicine", back_populates="medication_list")
    schedules = relationship("MedicationSchedule", back_populates="medication", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("duration_days > 0", name="check_positive_duration"),
        UniqueConstraint('medicine_id', 'user_id', 
                        name='unique_medication'),
    )