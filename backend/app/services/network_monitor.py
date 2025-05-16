# NetView/backend/app/services/network_monitor.py
import time
import psutil
import socket
from ping3 import ping
from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp
import ipaddress
from backend.app.database import get_all_devices, upsert_device, mark_offline
from backend.app.config import SYNC_INTERVAL_SECONDS

_last_scan_time = 0


def get_default_gateway_subnet():
    """
    Open a dummy UDP socket to a public IP to figure out which local
    interface & address would be used, then grab that interface’s netmask
    from psutil and compute the CIDR.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # we never actually send data; this just forces the kernel to pick an interface
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
    finally:
        sock.close()

    # find the matching psutil interface
    for iface, addrs in psutil.net_if_addrs().items():
        for snic in addrs:
            if snic.family == socket.AF_INET and snic.address == local_ip:
                netmask = snic.netmask
                network = ipaddress.IPv4Network(f"{local_ip}/{netmask}", strict=False)
                return str(network)

    return None


def discover_devices():
    global _last_scan_time

    subnet = get_default_gateway_subnet()
    if not subnet:
        # fallback: just return what’s in the DB
        return get_all_devices()

    arp_request = ARP(pdst=subnet)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = broadcast / arp_request
    answered = srp(packet, timeout=2, verbose=False)[0]

    seen_macs = set()
    for _, received in answered:
        mac = received.hwsrc
        ip = received.psrc
        seen_macs.add(mac)
        upsert_device(mac, ip)

    mark_offline(seen_macs)
    _last_scan_time = time.time()
    return get_all_devices()


def measure_latency(target="8.8.8.8"):
    delay = ping(target, unit="ms")
    return f"{int(delay)}ms" if delay else "timeout"


def get_network_stats():
    all_devices = get_all_devices()  # full history
    online_devices = [d for d in all_devices if d["online"]]
    current_online_devices = len(online_devices)
    latency = measure_latency()
    io = psutil.net_io_counters()

    print(f"[DEBUG get_network_stats] total={len(all_devices)} online={current_online_devices}")

    try:
        latency_ms = int(latency.replace("ms", "")) if latency != "timeout" else None
    except ValueError:
        latency_ms = None

    # Compute a simple health score
    health_score = 100
    if latency_ms is None:
        health_score -= 50
    elif latency_ms > 150:
        health_score -= 30
    elif latency_ms > 80:
        health_score -= 15

    if current_online_devices == 0:
        health_score -= 30

    if io.bytes_recv < 10_000 and io.bytes_sent < 10_000:
        health_score -= 15

    if health_score >= 85:
        network_health = "Excellent"
    elif health_score >= 65:
        network_health = "Good"
    elif health_score >= 40:
        network_health = "Fair"
    else:
        network_health = "Poor"

    return {
        "network_health": network_health,
        "total_devices": len(all_devices),
        "current_online_devices": current_online_devices,  # ← this line
        "average_latency": latency if latency_ms is not None else "timeout",
        "active_alerts": 0 if network_health in ["Excellent", "Good"] else 1,
        "next_update": f"{SYNC_INTERVAL_SECONDS}s",
        "bytes_sent": io.bytes_sent,
        "bytes_recv": io.bytes_recv,
    }
