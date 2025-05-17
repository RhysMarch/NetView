# backend/app/services/network_monitor.py

import time
import psutil
import socket
from ping3 import ping
from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp
import ipaddress

from backend.app.database import (
    get_all_devices,
    upsert_device,
    mark_offline,
    add_alert,
)
from backend.app.config import SYNC_INTERVAL_SECONDS

_last_scan_time = 0


def normalize_mac(mac: str) -> str:
    return mac.lower()


def get_default_gateway_subnet() -> str | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
    finally:
        sock.close()

    for iface, addrs in psutil.net_if_addrs().items():
        for snic in addrs:
            if snic.family == socket.AF_INET and snic.address == local_ip:
                return str(ipaddress.IPv4Network(f"{local_ip}/{snic.netmask}", strict=False))
    return None


def discover_devices():
    global _last_scan_time

    # 1) Snapshot of every device in the DB (with its last 'online' state)
    all_devices = get_all_devices()
    devices_by_mac = { normalize_mac(d["mac"]): d for d in all_devices }
    online_before = { mac for mac, d in devices_by_mac.items() if d["online"] }

    # 2) ARP scan of the subnet
    subnet = get_default_gateway_subnet()
    if not subnet:
        return all_devices

    answered = srp(
        Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=subnet),
        timeout=2,
        verbose=False
    )[0]

    seen = set()
    for _, pkt in answered:
        raw_mac = pkt.hwsrc
        mac     = normalize_mac(raw_mac)
        ip      = pkt.psrc
        seen.add(mac)

        # look up any custom name
        device = devices_by_mac.get(mac, {})
        label = device.get("name") or ip

        if mac not in devices_by_mac:
            # brand-new device
            add_alert(
                "new_device", mac, ip,
                f"New device detected: {mac} @ {label}"
            )
        elif mac not in online_before:
            # existed, but was offline — now back online
            add_alert(
                "device_back_online", mac, ip,
                f"Device back online: {mac} @ {label}"
            )

        # upsert (marks it online and updates timestamps)
        upsert_device(mac, ip)

    # 3) Mark all not-seen devices as offline
    mark_offline(seen)

    # 4) Fire “went offline” alerts for those that dropped out
    went_offline = online_before - seen
    for mac in went_offline:
        old = devices_by_mac[mac]
        label = old.get("name") or old["ip"]
        add_alert(
            "device_offline", mac, old["ip"],
            f"Device went offline: {mac} @ {label}"
        )

    _last_scan_time = time.time()
    return get_all_devices()


def measure_latency(target="8.8.8.8") -> str:
    delay = ping(target, unit="ms")
    return f"{int(delay)}ms" if delay else "timeout"


def get_network_stats():
    all_devices = get_all_devices()
    online = [d for d in all_devices if d["online"]]
    io = psutil.net_io_counters()

    # existing health logic...
    current_online = len(online)
    latency = measure_latency()

    health_score = 100
    if latency == "timeout":
        health_score -= 50
    else:
        v = int(latency.replace("ms", ""))
        if v > 150:
            health_score -= 30
        elif v > 80:
            health_score -= 15

    if current_online == 0:
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
        "network_health":         network_health,
        "total_devices":          len(all_devices),
        "current_online_devices": current_online,
        "average_latency":        latency,
        "active_alerts":          0 if network_health in ["Excellent", "Good"] else 1,
        "next_update":            f"{SYNC_INTERVAL_SECONDS}s",
        "bytes_sent":             io.bytes_sent,
        "bytes_recv":             io.bytes_recv,
    }
