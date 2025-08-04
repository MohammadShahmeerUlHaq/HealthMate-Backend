import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, 
    Enum, Text, Float, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.ext.mutable import MutableList

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    # attendant_email = Column(String(255), nullable=True)
    # attendant_emails = Column(ARRAY(String), nullable=True)
    attendant_emails = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    name = Column(String(100), nullable=False)
    password = Column(String(255), nullable=True)
    microsoft_firebase_uid = Column(String, unique=True, nullable=True)  # Firebase UID
    google_firebase_uid = Column(String, unique=True, nullable=True)  # Firebase UID
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    bp_systolic_min = Column(Integer, nullable=True)
    bp_systolic_max = Column(Integer, nullable=True)
    bp_diastolic_min = Column(Integer, nullable=True)
    bp_diastolic_max = Column(Integer, nullable=True)
    
    sugar_fasting_min = Column(Float, nullable=True)
    sugar_fasting_max = Column(Float, nullable=True)

    sugar_random_min = Column(Float, nullable=True)
    sugar_random_max = Column(Float, nullable=True)

    # Password reset fields
    reset_token = Column(String(255), nullable=True)
    reset_token_expiry = Column(DateTime(timezone=True), nullable=True)

    # Email verification fields
    email_verification_token = Column(String(255), nullable=True)
    email_verification_token_expiry = Column(DateTime(timezone=True), nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)

    # Relationships
    medications = relationship("Medication", back_populates="user", cascade="all, delete-orphan")
    bp_schedules = relationship("BloodPressureSchedule", back_populates="user", cascade="all, delete-orphan")
    sugar_schedules = relationship("SugarSchedule", back_populates="user", cascade="all, delete-orphan")
    # bp_logs = relationship("BloodPressureLog", back_populates="user", cascade="all, delete-orphan")
    # sugar_logs = relationship("SugarLog", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("LENGTH(name) > 0", name="check_name_not_empty"),
        CheckConstraint("email LIKE '%@%'", name="check_email_format"),
    )