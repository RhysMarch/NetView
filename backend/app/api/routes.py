# NetView/backend/app/api/routes.py
from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from backend.app.services.network_monitor import get_network_stats, discover_devices

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
    from backend.app.database import get_all_devices
    return get_all_devices()


def generate_topology():
    """
    Build a D3-friendly topology where each node carries its 'online' flag.
    """
    devices = discover_devices()
    gateway_ip = devices[0]["ip"] if devices else "192.168.1.1"

    nodes = [
        {
            "id": d["ip"],
            "label": d["ip"],
            "online": bool(d["online"]),
            "mac": d["mac"],  # Add MAC address
        }
        for d in devices
    ]

    links = [
        {"source": gateway_ip, "target": d["ip"]}
        for d in devices
    ]

    return {"nodes": nodes, "links": links}
