from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes import router, set_local_ip
from backend.app.database import init_db
from backend.app.services.network_monitor import _discover_and_update
import threading
import time

app = FastAPI()

# Allow frontend to talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock this down in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount our API routes under /api
app.include_router(router, prefix="/api")

# Ensure the SQLite DB and tables exist
init_db()


def _scan_loop():
    """Continuously re-scan in the background."""
    from backend.app.config import SYNC_INTERVAL_SECONDS
    while True:
        try:
            _discover_and_update()
        except Exception:
            pass
        time.sleep(SYNC_INTERVAL_SECONDS)


@app.on_event("startup")
async def startup_scanner():
    """Spawn a daemon thread that continuously rescans the network."""
    set_local_ip()
    t = threading.Thread(target=_scan_loop, daemon=True)
    t.start()
