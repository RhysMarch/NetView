import socket
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from backend.app.services.network_monitor import get_network_stats, discover_devices
from backend.app.database import get_all_devices, rename_device, get_alerts

router = APIRouter()


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


@router.get("/stats")
def fetch_stats():
    discover_devices()
    return get_network_stats()


@router.get("/topology")
async def get_topology():
    return await run_in_threadpool(lambda: generate_topology())


@router.get("/debug/devices")
async def get_all_devices_debug():
    return get_all_devices()


@router.get("/alerts")
async def api_get_alerts():
    return get_alerts()


class RenameRequest(BaseModel):
    name: str | None


@router.put("/devices/{mac}/rename", response_model=dict)
async def api_rename_device(mac: str, req: RenameRequest):
    devices = get_all_devices()
    if not any(d["mac"].lower() == mac.lower() for d in devices):
        raise HTTPException(404, "Device not found")
    rename_device(mac.lower(), req.name or "")
    return {"mac": mac.lower(), "name": req.name}


def generate_topology():
    devices = discover_devices()
    local_ip = get_local_ip()

    nodes = [
        {
            "id":         d["ip"],
            "label":      d["name"] or d["ip"],
            "online":     bool(d["online"]),
            "mac":        d["mac"],
            "is_gateway": (d["ip"] == local_ip),
        }
        for d in devices
    ]

    links = [{"source": local_ip, "target": d["ip"]} for d in devices]
    return {"nodes": nodes, "links": links}
