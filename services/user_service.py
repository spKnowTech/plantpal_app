# Business logic lives here
from sqlalchemy.orm import Session
from schemas.user import CreateUser
from models.user import User
from repositories.user_repo import get_user_by_email, create_user
from utils.helper import hash_password, verify_password


def register_user(user_data: CreateUser, db: Session):
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise ValueError("User already exists")

    hashed_pw = hash_password(user_data.password)
    user_data.password = hashed_pw
    user = User(**user_data.model_dump())
    return create_user(db, user)


def authenticate_user(email: str, password: str, db: Session):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
