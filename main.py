from fastapi import FastAPI, Request
from routers import user, plant, ai_bot, dashboard, photo
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
# Import models individually to avoid circular import issues

from models.user import User
from models.plant import Plant
from models.care_task import PlantCareTask, TaskCompletionHistory
from models.ai_bot import AILog, AIResponse, ConversationSession
from models.photo import PlantPhoto, PhotoDiagnosis, PhotoEmbedding, DiagnosisFeedback

app = FastAPI(
    title="PlantPal AI Assistant",
    description="A smart, plant-only assistant for plant care, Q&A, and management.",
    version="1.0.0"
)

# Mount static files (if you have a static directory)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates directory
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(user.router)
app.include_router(plant.router)
app.include_router(ai_bot.router)
app.include_router(dashboard.router)
app.include_router(photo.router)

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("home_page.html", {"request": request})

@app.get('/about', response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse('about.html', {"request": request})
