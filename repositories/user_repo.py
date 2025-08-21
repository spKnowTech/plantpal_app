from models.user import User
from sqlalchemy.orm import Session


def get_user_by_email(db: Session, email: str) -> User | None:
    """Retrieve a user by email."""
    try:
        return db.query(User).filter(User.email == email).first()
    except Exception as error:
        print(error)
        return None

def create_user(db: Session, user: User) -> User | None:
    """Create a new user in the database."""
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as error:
        print(error)
        return None