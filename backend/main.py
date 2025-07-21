from fastapi import FastAPI
from backend.routers import users, auth, plants, ai_chats
import uvicorn

app = FastAPI()


app.include_router(users.router)
app.include_router(auth.router)
app.include_router(plants.router)
app.include_router(ai_chats.router)

@app.get("/")
async def index():
   return {"message": "Hello World"}

if __name__ == "__main__":
   uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)