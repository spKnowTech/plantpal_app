import jwt
from datetime import datetime, timedelta, timezone
from schemas.user import TokenData
import database
from models.user import User
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from settings import Setting

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
SECRET_KEY = Setting.secret_key
ALGORITHM = Setting.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = Setting.access_token_expire_minutes


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def varify_access_token(token: str, credential_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credential_exception
        token_data = TokenData(id=str(user_id))
    except Exception:
        raise credential_exception
    return token_data


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(database.get_db)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Could not validate credentials",
                                         headers={"WWW-Authenticate": "Bearer"})
    token = varify_access_token(token, credential_exception)
    user = db.query(User).filter(User.id == token.id).first()
    return user
