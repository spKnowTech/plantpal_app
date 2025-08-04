from schemas.user import CreateUser
from models.user import User
from repositories.user_repo import get_user_by_email, create_user
from utils.helper import hash_password, verify_password
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def register_user(user_data: CreateUser, db: Session) -> User:
    """Register a new user if email is not taken."""
    try:
        existing = get_user_by_email(db, user_data.email)
        if existing is not None:
            raise ValueError("User already exists")
        user_data.password = hash_password(user_data.password)
        print(user_data)
        user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            password_hash=user_data.password,
            location=user_data.location
        )
        print(user.full_name)
        return create_user(db, user)
    except Exception as e:
        print(e)

def authenticate_user(email: str, password: str, db: Session) -> User | None:
    """Authenticate user by email and password."""
    try:
        user = get_user_by_email(db, email)
        if user and verify_password(password, user.password_hash):
            return user
        return None
    except Exception as e:
        print(e)
        

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User | None:
    """Get the current user from the session cookie. Returns None if unauthenticated."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except Exception:
        return None