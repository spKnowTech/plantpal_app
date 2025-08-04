from fastapi import APIRouter, Depends, status, HTTPException, Request, Response
from sqlalchemy.orm import Session
from schemas.plant import PlantCreate, PlantResponse, PlantUpdate
import services.plant_service as plant_service
from database import get_db
from services.user_service import get_current_user
from schemas.user import ResponseUser
from fastapi.templating import Jinja2Templates


router = APIRouter(prefix="/plants", tags=['Plants'])
templates = Jinja2Templates(directory="templates")

@router.post("/", response_model=PlantResponse, status_code=status.HTTP_201_CREATED)
async def create_plant(
    plant: PlantCreate,
    db: Session = Depends(get_db),
    user: ResponseUser = Depends(get_current_user)
) -> PlantResponse:
    """Create a new plant for the current user."""
    return await plant_service.create_plant_service(db, user.id, plant)

@router.get("/", response_model=list[PlantResponse])
async def get_all_plants(
    db: Session = Depends(get_db),
    user: ResponseUser = Depends(get_current_user)
) -> list[PlantResponse]:
    """Get all plants for the current user."""
    return await plant_service.get_user_plants_service(db, user.id)

@router.get("/{plant_id}", response_model=PlantResponse)
async def get_plant(
    plant_id: int,
    db: Session = Depends(get_db),
    user: ResponseUser = Depends(get_current_user)
) -> PlantResponse:
    """Get a specific plant by ID."""
    plant = await plant_service.get_plant_service(db, user.id, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant

@router.put("/{plant_id}", response_model=PlantResponse)
async def update_plant(
    plant_id: int,
    data: PlantUpdate,
    db: Session = Depends(get_db),
    user: ResponseUser = Depends(get_current_user)
) -> PlantResponse:
    """Update a plant's details."""
    updated = await plant_service.update_plant_service(db, user.id, plant_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Plant not found")
    return updated

@router.delete("/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plant(
    plant_id: int,
    db: Session = Depends(get_db),
    user: ResponseUser = Depends(get_current_user)
) -> Response:
    """Delete a plant."""
    deleted = await plant_service.delete_plant_service(db, user.id, plant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Plant not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
