from enum import Enum
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import List, Optional


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ForgotPassword(BaseModel):
    email: str


class VerifyEmail(BaseModel):
    token: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: Optional[str] = None  # Optional for Firebase users
    google_firebase_uid: Optional[str] = None  # Store Firebase UID if applicable
    microsoft_firebase_uid: Optional[str] = None  # Store Firebase UID if applicable

    attendant_emails: Optional[List[EmailStr]] = None

    bp_systolic_min: Optional[int] = None
    bp_systolic_max: Optional[int] = None
    bp_diastolic_min: Optional[int] = None
    bp_diastolic_max: Optional[int] = None
    
    sugar_fasting_min: Optional[int] = None
    sugar_fasting_max: Optional[int] = None

    sugar_random_min: Optional[int] = None
    sugar_random_max: Optional[int] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None

    attendant_emails: Optional[List[EmailStr]] = None

    bp_systolic_min: Optional[int]
    bp_systolic_max: Optional[int]
    bp_diastolic_min: Optional[int]
    bp_diastolic_max: Optional[int]
    
    sugar_fasting_min: Optional[int]
    sugar_fasting_max: Optional[int]

    sugar_random_min: Optional[int]
    sugar_random_max: Optional[int]


class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None  # Optional for Firebase users
    firebase_token: Optional[str] = None  # Store Firebase UID if applicable


class UserResponse(UserBase):
    # Attendant emails
    attendant_emails: Optional[List[EmailStr]] = None

    # Thresholds
    bp_systolic_min: Optional[int] = None
    bp_systolic_max: Optional[int] = None
    bp_diastolic_min: Optional[int] = None
    bp_diastolic_max: Optional[int] = None

    sugar_fasting_min: Optional[int] = None
    sugar_fasting_max: Optional[int] = None
    sugar_random_min: Optional[int] = None
    sugar_random_max: Optional[int] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
