from models.user import User
from sqlalchemy.orm import Session


def get_user_by_email(db: Session, email: str) -> User | None:
    """Retrieve a user by email."""
    user = db.query(User).filter(User.email == email).first()
    return user

def create_user(db: Session, user: User) -> User:
    """Create a new user in the database."""
    print("Service layer db:", db)
    print(user.full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user