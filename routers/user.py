from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from schemas.user import CreateUser
from forms.user_forms import UserCreateForm, UserLoginForm
from services.user_service import register_user, authenticate_user, get_current_user
from database import get_db
from services.ai_bot_service import clear_user_session


router = APIRouter(tags=['Users'])
templates = Jinja2Templates(directory="templates")

@router.get("/register", response_class=HTMLResponse)
async def show_register_form(request: Request) -> HTMLResponse:
    """Render the registration form."""
    return templates.TemplateResponse("register_profile.html", {"request": request})

@router.post('/register')
async def register_profile(
    request: Request,
    db: Session = Depends(get_db),
    form_data: UserCreateForm = Depends()
):
    """Handle user registration."""
    if form_data.password != form_data.confirm_password:
        return templates.TemplateResponse(
            "register_profile.html",
            {"request": request, "error": "Passwords do not match."}
        )
    try:
        user_data = CreateUser(
            full_name=form_data.full_name,
            email=form_data.email,
            password=form_data.password,
            location=form_data.location
        )
        register_user(user_data, db)
        response = RedirectResponse("/login", status_code=303)
        response.set_cookie("message", "Profile created successfully! Please log in.", max_age=5, path="/")
        response.set_cookie("message_type", "success", max_age=5, path="/")
        return response
    except ValueError as e:
        return templates.TemplateResponse("register_profile.html", {"request": request, "error": str(e)})
    except Exception:
        return templates.TemplateResponse("register_profile.html", {"request": request, "error": "Registration failed."})

# log in - GET
@router.get("/login")
async def show_login_form(request: Request) -> HTMLResponse:
    """Render the login form."""
    message = request.cookies.get("message")
    message_type = request.cookies.get("message_type")
    response = templates.TemplateResponse("login.html", {"request": request, "message": message, "message_type": message_type})
    response.delete_cookie("message")
    response.delete_cookie("message_type")
    return response

# log in - POST
@router.post("/login")
async def login(
    request: Request,
    form_data: UserLoginForm = Depends(),
    db: Session = Depends(get_db)
):
    """Handle user login."""
    user = authenticate_user(form_data.email, form_data.password, db)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        "user_id",
        str(user.id),
        httponly=True,
        secure=False,  # Set to True in production
        samesite="lax",
        max_age=86400  # 24 hour session expiration (increased from 6 hours)
    )
    response.set_cookie("message", f"Login successful! Welcome back, {user.full_name}!", max_age=5, path="/")
    response.set_cookie("message_type", "success", max_age=5, path="/")
    return response

# log out
@router.get("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """Handle user logout."""
    # Clear user session
    user = get_current_user(request, db)
    if user:
        clear_user_session(db, user.id)
    
    # Clear session cookie
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_token")
    return response