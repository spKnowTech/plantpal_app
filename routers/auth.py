from fastapi import APIRouter, Depends
from fastapi import status, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import user
import models
from utils import helper
import oauth2
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

router = APIRouter(tags=['Authentication'])


@router.post("/auth", response_model=users.Token)
def login(user_credential: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credential.username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")
    if not utils.varify_password(user_credential.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")
    access_token = oauth2.create_access_token(data={'user_id': user.id})
    return {'access_token': access_token, 'token_type': 'Bearer'}