from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from services.user_service import get_current_user
from database import get_db
from sqlalchemy.orm import Session
from repositories.plant_repo import get_user_plants, add_plant_for_user
from schemas.user import ResponseUser

# If you have a global templates instance, import it instead
templates = Jinja2Templates(directory='templates')

router = APIRouter(prefix="/dashboard", tags=['Dashboard'])

@router.get('/')
async def dashboard(
    request: Request, 
    user: ResponseUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        response = RedirectResponse("/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page.", max_age=5, path="/")
        response.set_cookie("message_type", "error", max_age=5, path="/")
        return response

    # Get user's plants
    plants = get_user_plants(db, user.id)
    
    message = request.cookies.get("message")
    message_type = request.cookies.get("message_type")
    
    response = templates.TemplateResponse('dashboard_page.html',
                                          context={
                                              'request': request, 
                                              'user': user, 
                                              'plants': plants,
                                              'message': message,
                                              'message_type': message_type
                                          })
    response.delete_cookie("message")
    response.delete_cookie("message_type")
    return response

@router.post('/add_plant')
async def add_plant(
    request: Request,
    plant_name: str = Form(...),
    location: str = Form(...),
    user: ResponseUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        response = RedirectResponse("/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page.", max_age=5, path="/")
        response.set_cookie("message_type", "error", max_age=5, path="/")
        return response

    try:
        # Add the plant
        add_plant_for_user(db, user.id, plant_name, location)
        
        # Redirect back to dashboard with success message
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie("message", f"Successfully added {plant_name}!", max_age=5, path="/")
        response.set_cookie("message_type", "success", max_age=5, path="/")
        return response
        
    except Exception as e:
        # Redirect back to dashboard with error message
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie("message", "Failed to add plant. Please try again.", max_age=5, path="/")
        response.set_cookie("message_type", "error", max_age=5, path="/")
        return response



