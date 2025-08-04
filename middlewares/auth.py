import firebase
from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
from fastapi.security import APIKeyHeader
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from database import get_db
from sqlalchemy.orm import Session
from models.users import User
from crud.users import get_or_create_firebase_user
from firebase_admin import auth as firebase_auth

from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2_scheme = APIKeyHeader(name="Authorization")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# def verify_access_token(token: str, db: Session):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: int = payload.get("user_id")
#         if user_id is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
#             )
#         return db.query(User).filter(User.id == user_id).first()
#     except (ExpiredSignatureError, InvalidTokenError):
#         return None

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return db.query(User).filter(User.id == user_id).first()
    except (ExpiredSignatureError, InvalidTokenError):
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )


# def get_current_user(
#     db: Session = Depends(get_db)
# ):
#     user = db.query(User).filter(User.email == "mohammadshahmeerulhaq@gmail.com").first()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
#         )
#     return user

# def get_current_user(
#     token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
# ):
#     user = verify_access_token(token, db)
#     if not user:
#         firebase_user = verify_firebase_token(token)
#         if firebase_user:
#             user = get_or_create_firebase_user(
#                 db,
#                 firebase_user["uid"],
#                 firebase_user["email"],
#                 firebase_user["firebase"]["sign_in_provider"],
#                 firebase_user["name"],
#             )
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
#         )
#     return user


def verify_firebase_token(token: str):
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print("🔥 Firebase token verification failed:", str(e))
        return None
