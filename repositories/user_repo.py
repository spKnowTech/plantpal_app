# DB operations live here

from models.user import User
from sqlalchemy.orm import Session

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
