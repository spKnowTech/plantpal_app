from fastapi import FastAPI, Request
from routers import user, plant, ai_chat, dashboard
from fastapi.staticfiles import StaticFiles
import os
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

# Set up templates directory
templates = Jinja2Templates(directory=os.path.join("templates"))

app.include_router(user.router)
app.include_router(plant.router)
app.include_router(ai_chat.router)
app.include_router(dashboard.router)

@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("home_page.html", {"request": request})
