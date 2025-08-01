from fastapi import FastAPI, Request
from routers import user, plant, ai_bot, dashboard
from fastapi.staticfiles import StaticFiles
import os
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="PlantPal AI Assistant",
    description="A smart, plant-only assistant for plant care, Q&A, and management.",
    version="1.0.0"
)

# Mount static files (if you have a static directory)
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates directory
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(user.router)
app.include_router(plant.router)
app.include_router(ai_chat.router)
app.include_router(dashboard.router)

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("home_page.html", {"request": request})

@app.get('/about', response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse('about.html', {"request": request})

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)