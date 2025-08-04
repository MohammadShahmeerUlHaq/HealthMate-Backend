from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models.users import User
from schemas.users import UserCreate, UserUpdate
from utilities.email import send_email
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import jwt
from fastapi import HTTPException, status
from pydantic import EmailStr,validate_email, ValidationError
from email_validator import validate_email, EmailNotValidError
load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def send_emailverification_email(recipient_email: str, message: str):

    subject = "HealthMate – Verify Your Email Address"

    body = f"""
    Hello,

    Thank you for signing up with HealthMate!

    To complete your registration and activate your account, please verify your email address by clicking the link below:

    {message}

    If you did not sign up for a HealthMate account, you can safely ignore this email.

    Best regards,
    Support Team
    """

    try:
        send_email(recipient_email, subject, body)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


def send_forgotpassword_email(recipient_email: str, message: str):

    subject = "HealthMate - Reset Your Password"

    body = f"""
    Hello,

    We received a request to reset your HealthMate account password.

    To proceed, please click the link below:

    "{message}"

    If you didn’t request this, you can safely ignore this email—your password will remain unchanged.

    Best regards,
    Support Team
    """

    try:
        send_email(recipient_email, subject, body)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


def create_access_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"user_id": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        return None
    return user


def create_user(db: Session, user_data: UserCreate):
    hashed_password = hash_password(user_data.password) if user_data.password else None
    user = User(
        email=user_data.email,
        name=user_data.name,
        password=hashed_password,

        # BP thresholds
        bp_systolic_min=user_data.bp_systolic_min,
        bp_systolic_max=user_data.bp_systolic_max,
        bp_diastolic_min=user_data.bp_diastolic_min,
        bp_diastolic_max=user_data.bp_diastolic_max,

        # Sugar thresholds
        sugar_fasting_min=user_data.sugar_fasting_min,
        sugar_fasting_max=user_data.sugar_fasting_max,
        sugar_random_min=user_data.sugar_random_min,
        sugar_random_max=user_data.sugar_random_max,

        # Attendant emails
        attendant_emails=user_data.attendant_emails,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_firebase_user(
    db: Session, firebase_uid: str, email: str, provider: str, name: str
):
    user = db.query(User).filter(User.email == email).first()

    if user:
        # Update the corresponding Firebase UID field if it's not already set
        if provider == "google.com" and not user.google_firebase_uid:
            user.google_firebase_uid = firebase_uid
        elif provider == "microsoft.com" and not user.microsoft_firebase_uid:
            user.microsoft_firebase_uid = firebase_uid

        db.commit()
        db.refresh(user)
        return user

    # No user with this email exists, create a new one
    user = User(
        email=email,
        name=name,
        google_firebase_uid=firebase_uid if provider == "google" else None,
        microsoft_firebase_uid=firebase_uid if provider == "microsoft" else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, user_data: UserUpdate):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    # Update fields if present
    if user_data.name is not None:
        user.name = user_data.name

    if user_data.attendant_emails is not None:
        user.attendant_emails = user_data.attendant_emails

    if user_data.bp_systolic_min is not None:
        user.bp_systolic_min = user_data.bp_systolic_min
    if user_data.bp_systolic_max is not None:
        user.bp_systolic_max = user_data.bp_systolic_max
    if user_data.bp_diastolic_min is not None:
        user.bp_diastolic_min = user_data.bp_diastolic_min
    if user_data.bp_diastolic_max is not None:
        user.bp_diastolic_max = user_data.bp_diastolic_max

    if user_data.sugar_fasting_min is not None:
        user.sugar_fasting_min = user_data.sugar_fasting_min
    if user_data.sugar_fasting_max is not None:
        user.sugar_fasting_max = user_data.sugar_fasting_max
    if user_data.sugar_random_min is not None:
        user.sugar_random_min = user_data.sugar_random_min
    if user_data.sugar_random_max is not None:
        user.sugar_random_max = user_data.sugar_random_max

    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


    user = db.query(User).filter(User.id == user_id).first()
    if user:
        if user_data.name is not None:
            user.name = user_data.name
        db.commit()
        db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user


def add_attendant_email(db: Session, user_id: int, email: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    try:
        validate_email(email)
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid email format")

    if user.attendant_emails is None:
        user.attendant_emails = []

    if email.lower() not in user.attendant_emails:
        user.attendant_emails.append(email.lower())
        db.commit()
        db.refresh(user)

    return user


def delete_attendant_email(db: Session, user_id: int, email: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.attendant_emails:
        return None

    if email.lower() in user.attendant_emails:
        user.attendant_emails.remove(email)
        db.commit()
        db.refresh(user)

    return user


def update_single_attendant_email(db: Session, user_id: int, old_email: str, new_email: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    if not user.attendant_emails:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendant emails configured."
        )

    try:
        validate_email(old_email)
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid old email format")
    
    try:
        validate_email(new_email)
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid new email format")

    if old_email.lower() not in user.attendant_emails:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Old email not found in user's attendant emails."
        )

    if new_email.lower() in user.attendant_emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New email already exists in user's attendant emails."
        )

    index = user.attendant_emails.index(old_email)
    user.attendant_emails[index] = new_email.lower()
    db.commit()
    db.refresh(user)
    return user

def send_email_to_attendants(attendant_emails: list[str], subject: str, body: str):
    if not attendant_emails:
        print("⚠️ No attendant emails provided.")
        return {"sent_to": [], "failed": []}

    sent_emails = []
    failed_emails = []

    for email in attendant_emails:
        try:
            send_email(email, subject, body)
            sent_emails.append(email)
        except Exception as e:
            print(f"❌ Failed to send email to {email}: {e}")
            failed_emails.append({"email": email, "error": str(e)})

    return {"sent_to": sent_emails, "failed": failed_emails}

# def update_user(db: Session, user_id: int, user_data: UserUpdate):