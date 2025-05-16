# NetView/backend/app/api/routes.py
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from backend.app.services.network_monitor import get_network_stats, discover_devices
from backend.app.database import get_all_devices, rename_device

router = APIRouter()


@router.get("/stats")
def fetch_stats():
    # 1) Trigger a fresh scan right now
    discover_devices()
    # 2) Return up-to-date stats (including next_update)
    return get_network_stats()


@router.get("/topology")
async def get_topology():
    # Always recompute topology from the latest scan
    return await run_in_threadpool(lambda: generate_topology())


@router.get("/debug/devices")
async def get_all_devices_debug():
    return get_all_devices()


class RenameRequest(BaseModel):
    name: str | None  # pass empty or null to clear the name


@router.put("/devices/{mac}/rename", response_model=dict)
async def api_rename_device(mac: str, req: RenameRequest):
    # verify device exists
    devices = get_all_devices()
    if not any(d["mac"].lower() == mac.lower() for d in devices):
        raise HTTPException(status_code=404, detail="Device not found")

    rename_device(mac.lower(), req.name or "")
    return {"mac": mac.lower(), "name": req.name}


def generate_topology():
    """
    Build a D3-friendly topology where each node carries its 'online' flag
    and uses the user-defined 'name' as the label if present.
    """
    devices = discover_devices()
    gateway_ip = devices[0]["ip"] if devices else "192.168.1.1"

    nodes = [
        {
            "id":     d["ip"],
            "label":  d["name"] or d["ip"],
            "online": bool(d["online"]),
            "mac":    d["mac"],
        }
        for d in devices
    ]

    links = [{"source": gateway_ip, "target": d["ip"]} for d in devices]

    return {"nodes": nodes, "links": links}
