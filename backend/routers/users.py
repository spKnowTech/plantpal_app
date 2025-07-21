from backend.utils import hash_password
from fastapi import status, HTTPException
from fastapi import Depends, APIRouter
from backend.schemas import users
from backend import models
from backend.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=['Users'])


@router.post('/', status_code=status.HTTP_201_CREATED,
             response_model=users.ResponseUser)
def register_profile(user: users.CreateUser,
                db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    user.password = hashed_password
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get('/{user_id}', response_model=users.ResponseUser)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {user_id} is not found.")
    return user