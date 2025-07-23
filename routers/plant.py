from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.orm import Session
from schemas.plant import PlantCreate, PlantResponse, PlantUpdate
import services.plant_service as plant_service
from database import get_db
from oauth2 import get_current_user
from schemas.user import ResponseUser
from fastapi.templating import Jinja2Templates


router = APIRouter(prefix="/plants", tags=['Plants'])
templates = Jinja2Templates(directory="templates")

@router.post("/", response_model=PlantResponse, status_code=status.HTTP_201_CREATED)
def create_plant(plant: PlantCreate, db: Session = Depends(get_db), user: ResponseUser = Depends(get_current_user)):
    return plant_service.create_plant_service(db, user.id, plant)


@router.get("/", response_model=list[PlantResponse])
def get_all_plants(db: Session = Depends(get_db), user: ResponseUser = Depends(get_current_user)):
    return plant_service.get_user_plants_service(db, user.id)


@router.get("/{plant_id}", response_model=PlantResponse)
def get_plant(plant_id: int, db: Session = Depends(get_db), user: ResponseUser = Depends(get_current_user)):
    plant = plant_service.get_plant_service(db, user.id, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.put("/{plant_id}", response_model=PlantResponse)
def update_plant(plant_id: int, data: PlantUpdate, db: Session = Depends(get_db), user: ResponseUser = Depends(get_current_user)):
    updated = plant_service.update_plant_service(db, user.id, plant_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Plant not found")
    return updated


@router.delete("/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plant(plant_id: int, db: Session = Depends(get_db), user: ResponseUser = Depends(get_current_user)):
    deleted = plant_service.delete_plant_service(db, user.id, plant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Plant not found")
    return

@router.get("/dashboard")
def dashboard(request: Request, db=Depends(get_db), user=Depends(get_current_user)):
    plants = plant_service.get_user_plants_service(db, user.id)
    return templates.TemplateResponse("plant_list.html", {"request": request, "plants": plants})