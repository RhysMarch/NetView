# NetView/backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes import router
from backend.app.database import init_db
import asyncio
from backend.app.services.network_monitor import discover_devices
from backend.app.config import SYNC_INTERVAL_SECONDS

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

# Initialise DB before app starts
init_db()


# Background scanner task
async def background_scan():
    while True:
        try:
            discover_devices()
        except Exception as e:
            print(f"[Scan Error] {e}")
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_scan())
