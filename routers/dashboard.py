from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from services.user_service import get_current_user
from database import get_db
from sqlalchemy.orm import Session
from repositories.plant_repo import get_user_plants, create_plant
from schemas.plant import PlantCreate
from schemas.user import ResponseUser
from schemas.care_task import PlantCareTaskCreate
from services.care_task_service import (
    get_tasks_statistics_service,
    create_care_task_service, complete_task_service
)
from datetime import date

# If you have a global templates instance, import it instead
templates = Jinja2Templates(directory='templates')

router = APIRouter(prefix="/dashboard", tags=['Dashboard'])


@router.get('/')
async def dashboard(
        request: Request,
        user: ResponseUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Render the main dashboard page with user's plants and task data."""
    if not user:
        response = RedirectResponse("/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page.", max_age=5, path="/")
        response.set_cookie("message_type", "error", max_age=5, path="/")
        return response

    # Get user's plants
    plants = get_user_plants(db, user.id)
    # Get task statistics
    task_statistics = get_tasks_statistics_service(db, user.id)
    message = request.cookies.get("message")
    message_type = request.cookies.get("message_type")

    context = {
        'request': request,
        'user': user,
        'plants': plants,
        'task_statistics': task_statistics,
        'message': message,
        'message_type': message_type
    }
    response = templates.TemplateResponse('dashboard_page.html', context=context)
    response.delete_cookie("message")
    response.delete_cookie("message_type")
    return response

@router.post('/tasks')
async def create_task(
    request: Request,
    db: Session = Depends(get_db),
    user: ResponseUser = Depends(get_current_user)
):
    """Create a new care task."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Parse JSON manually to see what we're getting
        raw_data = await request.json()
        # Convert data types manually
        task_data = {
            "plant_id": int(raw_data.get("plant_id")),
            "task_type": raw_data.get("task_type"),
            "title": raw_data.get("title"),
            "description": raw_data.get("description") or None,
            "recurrence_type": raw_data.get("recurrence_type"),
            "frequency_days": int(raw_data.get("frequency_days")),
            "due_date": date.today(),
            "user_id": user.id
        }
        print(task_data)
        # Create the task using the service directly
        task_create = PlantCareTaskCreate(**task_data)
        created_task = create_care_task_service(db, task_create, user.id)
        if not created_task:
            raise HTTPException(status_code=400, detail="Failed to create task - plant may not exist or you don't have permission")
        return created_task
        
    except ValueError as e:
        print(f"ValueError: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid data: {str(e)}")
    except Exception as e:
        print(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.post('/tasks/{task_id}/complete')
async def complete_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: ResponseUser = Depends(get_current_user)
):
    """Mark a task as completed."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        body = await request.json()
        is_completed = body.get("is_completed", True)
        complete_task_service(db, task_id, user.id, is_completed)
        return {"message": "Task status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task status: {str(e)}")


@router.post('/add_plant')
async def add_plant(
        request: Request,
        plant_name: str = Form(...),
        location: str = Form(...),
        user: ResponseUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Handle adding a new plant to the user's collection."""
    if not user:
        response = RedirectResponse("/login", status_code=303)
        response.set_cookie("message", "Please log in to access this page.", max_age=5, path="/")
        response.set_cookie("message_type", "error", max_age=5, path="/")
        return response

    try:
        # Create plant data
        plant_data = PlantCreate(
            name=plant_name,
            location=location
        )

        # Add the plant using the updated function
        create_plant(db, plant_data, user.id)

        # Redirect back to dashboard with success message
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie("message", f"Successfully added {plant_name}!", max_age=5, path="/")
        response.set_cookie("message_type", "success", max_age=5, path="/")
        return response

    except Exception as e:
        # Redirect back to dashboard with error message
        print(f"Error adding plant: {e}")
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie("message", "Failed to add plant. Please try again.", max_age=5, path="/")
        response.set_cookie("message_type", "error", max_age=5, path="/")
        return response

