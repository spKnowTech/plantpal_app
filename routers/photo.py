from fastapi import APIRouter, Request, Depends, File, UploadFile, Form, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services.user_service import get_current_user
from schemas.user import ResponseUser
from services.photo_service import (
    upload_plant_photo, get_user_photos_with_diagnoses, delete_user_photo,
    get_user_photo_by_id, get_photo_diagnosis, get_analysis_statistics
)
from repositories.plant_repo import get_user_plants
from plant_pal_bot.ai_bot_chat import analyze_plant_photo_with_rag
from services.ai_bot_service import save_user_message_service, save_bot_message_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/photo_gallery", response_class=HTMLResponse)
async def photo_gallery(
        request: Request,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user)
):
    """Display user's photo gallery with diagnoses."""
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        # Get user's photos with diagnoses
        photos_with_diagnoses = get_user_photos_with_diagnoses(db, user.id, limit=50)

        # Get user's plants for context
        user_plants = get_user_plants(db, user.id)

        # Get analysis statistics
        stats = get_analysis_statistics(db, user.id)

        return templates.TemplateResponse("photo_gallery.html", {
            "request": request,
            "user": user,
            "photos_with_diagnoses": photos_with_diagnoses,
            "user_plants": user_plants,
            "stats": stats
        })

    except Exception as e:
        print(f"Error in photo_gallery: {str(e)}")
        return templates.TemplateResponse("photo_gallery.html", {
            "request": request,
            "user": user,
            "photos_with_diagnoses": [],
            "user_plants": [],
            "stats": {},
            "error": "Failed to load photo gallery"
        })


@router.post("/upload_photo")
async def upload_photo(
        request: Request,
        file: UploadFile = File(...),
        plant_id: Optional[int] = Form(None),
        upload_context: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user)
):
    """Handle photo upload."""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    try:
        # Upload and save photo
        photo_response = await upload_plant_photo(
            db=db,
            file=file,
            user_id=user.id,
            plant_id=plant_id,
            upload_context=upload_context
        )

        return JSONResponse(content={
            "success": True,
            "message": "Photo uploaded successfully! 📸",
            "photo_id": photo_response.id,
            "photo_url": f"/static/uploads/plant_photos/{photo_response.image_path.split('/')[-1]}"
        })

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.detail}
        )
    except Exception as e:
        print(f"Error uploading photo: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to upload photo"}
        )


@router.post("/analyze_photo/{photo_id}")
async def analyze_photo(
        photo_id: int,
        user_message: Optional[str] = Form("Please analyze this photo"),
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user)
):
    """Analyze a specific photo with AI."""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    try:
        # Verify photo belongs to user
        photo = get_user_photo_by_id(db, photo_id, user.id)
        if not photo:
            return JSONResponse(
                status_code=404,
                content={"error": "Photo not found"}
            )

        # Save user message for chat history
        save_user_message_service(db, user.id, f"Analyze photo #{photo_id}: {user_message}")

        # Analyze photo with RAG
        analysis_result = analyze_plant_photo_with_rag(db, user.id, user_message, photo_id)

        # Save bot response for chat history
        save_bot_message_service(db, user.id, analysis_result.ai_response)

        return JSONResponse(content={
            "success": True,
            "analysis": analysis_result.ai_response,
            "photo_id": photo_id
        })

    except Exception as e:
        print(f"Error analyzing photo {photo_id}: {str(e)}")
        error_response = f"❌ Analysis failed: {str(e)}"
        save_bot_message_service(db, user.id, error_response)

        return JSONResponse(
            status_code=500,
            content={"error": error_response}
        )


@router.delete("/delete_photo/{photo_id}")
async def delete_photo(
        photo_id: int,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user)
):
    """Delete a photo and its associated data."""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    try:
        success = delete_user_photo(db, photo_id, user.id)

        if success:
            return JSONResponse(content={
                "success": True,
                "message": "Photo deleted successfully"
            })
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "Photo not found"}
            )

    except Exception as e:
        print(f"Error deleting photo {photo_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to delete photo"}
        )


@router.get("/photo/{photo_id}/diagnosis")
async def get_photo_diagnosis_endpoint(
        photo_id: int,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user)
):
    """Get diagnosis for a specific photo."""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    try:
        # Verify photo belongs to user
        photo = get_user_photo_by_id(db, photo_id, user.id)
        if not photo:
            return JSONResponse(
                status_code=404,
                content={"error": "Photo not found"}
            )

        # Get diagnosis
        diagnosis = get_photo_diagnosis(db, photo_id, user.id)

        if diagnosis:
            return JSONResponse(content={
                "success": True,
                "diagnosis": {
                    "id": diagnosis.id,
                    "diagnosis_text": diagnosis.diagnosis_text,
                    "confidence_score": diagnosis.confidence_score,
                    "identified_issues": diagnosis.identified_issues,
                    "recommended_actions": diagnosis.recommended_actions,
                    "treatment_outcome": diagnosis.treatment_outcome,
                    "created_at": diagnosis.created_at.isoformat()
                }
            })
        else:
            return JSONResponse(content={
                "success": True,
                "diagnosis": None,
                "message": "No diagnosis available for this photo"
            })

    except Exception as e:
        print(f"Error getting diagnosis for photo {photo_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get diagnosis"}
        )


@router.get("/photo_upload", response_class=HTMLResponse)
async def photo_upload_page(
        request: Request,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user)
):
    """Display photo upload page."""
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        # Get user's plants for plant selection
        user_plants = get_user_plants(db, user.id)

        return templates.TemplateResponse("photo_upload.html", {
            "request": request,
            "user": user,
            "user_plants": user_plants
        })

    except Exception as e:
        print(f"Error in photo_upload_page: {str(e)}")
        return templates.TemplateResponse("photo_upload.html", {
            "request": request,
            "user": user,
            "user_plants": [],
            "error": "Failed to load upload page"
        })


# API endpoints for integration with chat system
@router.get("/api/user_photos")
async def get_user_photos_api(
        limit: int = 20,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user)
):
    """API endpoint to get user's photos."""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    try:
        photos_with_diagnoses = get_user_photos_with_diagnoses(db, user.id, limit=limit)

        photos_data = []
        for item in photos_with_diagnoses:
            photo_data = {
                "id": item.photo.id,
                "image_path": item.photo.image_path,
                "original_filename": item.photo.original_filename,
                "upload_context": item.photo.upload_context,
                "diagnosis_status": item.photo.diagnosis_status,
                "created_at": item.photo.created_at.isoformat(),
                "plant_name": item.plant_name,
                "has_diagnosis": item.diagnosis is not None,
                "thumbnail_url": f"/static/uploads/thumbnails/thumb_{item.photo.image_path.split('/')[-1]}"
            }

            if item.diagnosis:
                photo_data["diagnosis"] = {
                    "confidence_score": item.diagnosis.confidence_score,
                    "treatment_outcome": item.diagnosis.treatment_outcome,
                    "created_at": item.diagnosis.created_at.isoformat()
                }

            photos_data.append(photo_data)

        return JSONResponse(content={
            "success": True,
            "photos": photos_data
        })

    except Exception as e:
        print(f"Error in get_user_photos_api: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get photos"}
        )


@router.post("/api/quick_analyze")
async def quick_analyze_recent_photo(
        user_message: str = Form("Analyze my recent photo"),
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user)
):
    """Quick analyze the most recent photo."""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    try:
        from services.photo_service import get_user_photos_list

        # Get most recent photo
        recent_photos = get_user_photos_list(db, user.id, limit=1)

        if not recent_photos:
            return JSONResponse(
                status_code=404,
                content={"error": "No photos found. Please upload a photo first."}
            )

        photo_id = recent_photos[0].id

        # Save user message
        save_user_message_service(db, user.id, f"Quick analyze: {user_message}")

        # Analyze photo
        analysis_result = analyze_plant_photo_with_rag(db, user.id, user_message, photo_id)

        # Save bot response
        save_bot_message_service(db, user.id, analysis_result.ai_response)

        return JSONResponse(content={
            "success": True,
            "analysis": analysis_result.ai_response,
            "photo_id": photo_id
        })

    except Exception as e:
        print(f"Error in quick_analyze_recent_photo: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to analyze photo"}
        )