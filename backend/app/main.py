# NetView/backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes import router
from backend.app.database import init_db

app = FastAPI()

# Allow frontend to talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # lock this down in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount our API routes under /api
app.include_router(router, prefix="/api")

# Ensure the SQLite DB and tables exist
init_db()
