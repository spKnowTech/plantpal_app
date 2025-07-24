import jwt
from datetime import datetime, timedelta, timezone
from schemas.user import TokenData
from fastapi.security import OAuth2PasswordBearer
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


