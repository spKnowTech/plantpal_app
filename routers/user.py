# All FastAPI route logic
from utils.helper import hash_password
from sqlalchemy.orm import Session
from fastapi import status, HTTPException
from fastapi import Depends, APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from schemas.user import ResponseUser, CreateUser
import models
from database import get_db
from forms.user_forms import UserCreateForm, UserLoginForm
from services.user_service import register_user, authenticate_user
from oauth2 import create_access_token


router = APIRouter(prefix="/register", tags=['Users'])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def show_register_form(request: Request):
    return templates.TemplateResponse("register_profile.html", {"request": request})


@router.post('/')
def register_profile(request: Request,
                     db: Session = Depends(get_db),
                     form_data: UserCreateForm = Depends()):
    try:
        user_data = CreateUser(full_name=form_data.full_name,
                               email=form_data.email,
                               password=hash_password(form_data.password),
                               location=form_data.location)

        register_user(user_data, db)
        return RedirectResponse("/login", status_code=303)
    except ValueError as e:
        return templates.TemplateResponse("register_profile.html", {"request": request, "error": str(e)})


@router.get("/login", response_class=HTMLResponse)
def show_login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(
    request: Request,
    form_data: UserLoginForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(form_data.email, form_data.password, db)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    token = create_access_token({"sub": user.email})
    response = RedirectResponse("/", status_code=303)
    response.set_cookie("access_token", token, httponly=True)
    return response



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

