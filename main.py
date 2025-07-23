from fastapi import FastAPI
from routers import user, auth, plant, ai_chat
from fastapi.staticfiles import StaticFiles
import os
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join("static")), name="static")

# Set up templates directory
templates = Jinja2Templates(directory=os.path.join("templates"))

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(plant.router)
app.include_router(ai_chat.router)

@app.get("/")
async def index():
   return {"message": "Hello World"}
