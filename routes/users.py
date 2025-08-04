import os
import jwt
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db

from crud.users import (
    authenticate_user,
    create_user,
    get_user,
    update_user,
    delete_user,
    get_or_create_firebase_user,
    send_forgotpassword_email,
    send_emailverification_email,
    hash_password,
    create_access_token,
    add_attendant_email,
    delete_attendant_email,
    update_single_attendant_email,
    send_email_to_attendants
)

from schemas.users import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    PasswordChangeRequest,
    ResetPasswordRequest,
    VerifyEmail,
    ForgotPassword,
)

from models.users import User
from middlewares.auth import get_current_user, verify_firebase_token

load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

import secrets
from datetime import datetime, timedelta


@router.post("/forgot-password")
def forgot_password(data: ForgotPassword, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate token
    token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)

    user.reset_token = token
    user.reset_token_expiry = expiry
    db.commit()

    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    send_forgotpassword_email(data.email, reset_link)

    print(f"Password reset link: {reset_link}")

    return {"message": "Reset link has been sent to your email."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == data.token).first()
    if (
        not user
        or not user.reset_token_expiry
        or user.reset_token_expiry < datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.password = hash_password(data.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()

    return {"message": "Password reset successfully. Login using the new password."}


@router.post("/change-password")
def change_password(
    request: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not request.old_password or not request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old and new passwords are required",
        )

    # Verify old password
    if not pwd_context.verify(request.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Old password is incorrect",
        )

    # Update password
    current_user.password = hash_password(request.new_password)
    db.commit()
    db.refresh(current_user)

    return {"message": "Password changed successfully"}


@router.post("/login", status_code=status.HTTP_200_OK)
def login_user(user: UserLogin, db: Session = Depends(get_db)):

    if user.firebase_token:
        firebase_user = verify_firebase_token(user.firebase_token)
        print("FIREBASE USER: ", firebase_user)
        if not firebase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase token",
            )
        print(
            firebase_user["uid"],
            firebase_user["email"],
            firebase_user["firebase"]["sign_in_provider"],
            firebase_user["name"],
        )
        if firebase_user["firebase"]["sign_in_provider"] not in [
            "google.com",
            "microsoft.com",
        ]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sign-in provider not allowed. Please use Google or Microsoft.",
            )
        current_user = get_or_create_firebase_user(
            db,
            firebase_user["uid"],
            firebase_user["email"],
            firebase_user["firebase"]["sign_in_provider"],
            firebase_user["name"],
        )
    else:
        if not user.email or not user.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required",
            )
        current_user = authenticate_user(db, user.email, user.password)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not current_user.email_verified:
            token = secrets.token_urlsafe(32)
            expiry = datetime.now(timezone.utc) + timedelta(hours=1)

            current_user.email_verification_token = token
            current_user.email_verification_token_expiry = expiry
            db.commit()

            email_verification_link = f"{FRONTEND_URL}/verify-email?token={token}"

            send_emailverification_email(current_user.email, email_verification_link)

            print(f"Email verification link: {email_verification_link}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your email address hasn't been verified yet. Please check your inbox for our verification email and click the link to activate your account.",
            )

    access_token = create_access_token(current_user.id)
    return {"message": "Login successful", "accessToken": access_token, "token_type": "bearer"}


# @router.get("/verify", status_code=status.HTTP_200_OK)
# def verify(
#     db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
# ):
#     return {"message": "access granted"}


@router.post("")
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    if not user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required",
        )
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        if existing_user.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        else:
            hashed_password = hash_password(user.password) if user.password else None
            existing_user.password = hashed_password
            db.commit()
            db.refresh(existing_user)
            return {
                "message": "Signup successful. Please check your inbox for our verification email and click the link to activate your account."
            }
    else:
        existing_user = create_user(db, user)

    token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)

    existing_user.email_verification_token = token
    existing_user.email_verification_token_expiry = expiry
    db.commit()

    email_verification_link = f"{FRONTEND_URL}/verify-email?token={token}"

    send_emailverification_email(existing_user.email, email_verification_link)

    print(f"Email verification link: {email_verification_link}")

    return {
        "message": "Signup successful. Please check your inbox for our verification email and click the link to activate your account."
    }


@router.post("/verify-email")
def verify_email(data: VerifyEmail, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email_verification_token == data.token).first()
    if (
        not user
        or not user.email_verification_token_expiry
        or user.email_verification_token_expiry < datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.email_verification_token = None
    user.email_verification_token_expiry = None
    user.email_verified = True
    db.commit()

    access_token = create_access_token(user.id)
    return {"message": "Email Verified", "accessToken": access_token}


@router.get("", response_model=UserResponse)
def read_user(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    db_user = get_user(db, current_user.id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("", response_model=UserResponse)
def update_existing_user(
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated_user = update_user(db, current_user.id, user)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.delete("")
def delete_existing_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted_user = delete_user(db, current_user.id)
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@router.post("/attendant-emails", response_model=UserResponse)
def add_attendant(email: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = add_attendant_email(db, current_user.id, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/attendant-emails", response_model=UserResponse)
def remove_attendant(email: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = delete_attendant_email(db, current_user.id, email)
    if not user:
        raise HTTPException(status_code=404, detail="User or email not found")
    return user


@router.patch("/attendant-emails", response_model=UserResponse)
def update_attendant_email(old_email: str, new_email: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = update_single_attendant_email(db, current_user.id, old_email, new_email)
    if not user:
        raise HTTPException(status_code=404, detail="User or email not found")
    return user

@router.post("/send-email-to-attendants")
def send_email_to_attendants_route(
    subject: str,
    body: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return send_email_to_attendants(
        attendant_emails=current_user.attendant_emails,
        subject=subject,
        body=body
    )