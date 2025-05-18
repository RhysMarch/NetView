import time
import datetime
import psutil
import socket
import requests
from ping3 import ping
from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp
import ipaddress

from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.app.database import (
    get_all_devices,
    upsert_device,
    mark_offline,
    add_alert,
)
from backend.app.config import SYNC_INTERVAL_SECONDS

_LOOKUP_WORKERS = 10
_VENDOR_TTL = 24 * 3600  # seconds
_HOST_TTL = 1 * 3600  # seconds


def normalize_mac(mac: str) -> str:
    return mac.lower()


def get_default_gateway_subnet() -> str | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
    finally:
        sock.close()

    for addrs in psutil.net_if_addrs().values():
        for snic in addrs:
            if snic.family == socket.AF_INET and snic.address == local_ip:
                return str(ipaddress.IPv4Network(f"{local_ip}/{snic.netmask}", strict=False))
    return None


def _reverse_dns(ip: str) -> str | None:
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return None


def _vendor_api(mac: str) -> str | None:
    try:
        resp = requests.get(f"https://api.macvendors.com/{mac}", timeout=2)
        if resp.status_code == 200:
            return resp.text.strip()
    except requests.RequestException:
        pass
    return None


def _needs_refresh(last_seen_iso: str | None, ttl: int) -> bool:
    if not last_seen_iso:
        return True
    try:
        dt = datetime.datetime.fromisoformat(last_seen_iso)
        return (time.time() - dt.timestamp()) > ttl
    except Exception:
        return True


def _do_lookup(mac, ip, do_host, do_vend, existing):
    hostname = _reverse_dns(ip) if do_host else existing.get("hostname")
    vendor = _vendor_api(mac) if do_vend else existing.get("vendor")
    return mac, ip, hostname, vendor


def _discover_and_update():
    """Run one full ARP/DNS/vendor sweep and write into the DB."""
    all_devices = get_all_devices()
    by_mac = {normalize_mac(d["mac"]): d for d in all_devices}
    online_before = {m for m, d in by_mac.items() if d["online"]}

    subnet = get_default_gateway_subnet()
    if not subnet:
        return all_devices

    answered = srp(
        Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet),
        timeout=2, verbose=False
    )[0]

    seen = set()
    tasks = []
    for _, pkt in answered:
        mac = normalize_mac(pkt.hwsrc)
        ip = pkt.psrc
        seen.add(mac)

        dev = by_mac.get(mac, {})
        last_seen = dev.get("last_seen")
        do_host = not dev.get("hostname") or _needs_refresh(last_seen, _HOST_TTL)
        do_vend = not dev.get("vendor") or _needs_refresh(last_seen, _VENDOR_TTL)
        tasks.append((mac, ip, do_host, do_vend, dev))

    # parallel DNS + vendor lookups
    results = []
    with ThreadPoolExecutor(max_workers=_LOOKUP_WORKERS) as ex:
        futures = {
            ex.submit(_do_lookup, mac, ip, dh, dv, dev): (mac, ip)
            for mac, ip, dh, dv, dev in tasks
        }
        for fut in as_completed(futures):
            results.append(fut.result())

    # write results & generate alerts
    for mac, ip, hostname, vendor in results:
        existing = by_mac.get(mac)
        label = (existing.get("name") or hostname or ip) if existing else hostname or ip

        if not existing:
            add_alert("new_device", mac, ip, f"New device detected: {mac} @ {label}")
        elif mac not in online_before:
            add_alert("device_back_online", mac, ip, f"Device back online: {mac} @ {label}")

        upsert_device(mac, ip, hostname, vendor)

    mark_offline(seen)

    went_off = online_before - seen
    for mac in went_off:
        old = by_mac[mac]
        label = old.get("name") or old.get("hostname") or old["ip"]
        add_alert("device_offline", mac, old["ip"], f"Device went offline: {mac} @ {label}")

    return get_all_devices()


def discover_devices_once():
    """
    **Always** return the latest snapshot from the DB.
    Never trigger any network I/O here—that’s now fully backgrounded.
    """
    return get_all_devices()


def measure_latency(target="8.8.8.8") -> str:
    delay = ping(target, unit="ms")
    return f"{int(delay)}ms" if delay else "timeout"


def get_network_stats(devices):
    online = [d for d in devices if d["online"]]
    io = psutil.net_io_counters()
    latency = measure_latency()

    score = 100
    if latency == "timeout":
        score -= 50
    else:
        v = int(latency.replace("ms", ""))
        if v > 150:
            score -= 30
        elif v > 80:
            score -= 15

    if len(online) == 0:        score -= 30
    if io.bytes_recv < 10_000 and io.bytes_sent < 10_000:
        score -= 15

    if score >= 85:
        health = "Excellent"
    elif score >= 65:
        health = "Good"
    elif score >= 40:
        health = "Fair"
    else:
        health = "Poor"

    return {
        "network_health": health,
        "total_devices": len(devices),
        "current_online_devices": len(online),
        "average_latency": latency,
        "active_alerts": 0 if health in ["Excellent", "Good"] else 1,
        "next_update": f"{SYNC_INTERVAL_SECONDS}s",
        "bytes_sent": io.bytes_sent,
        "bytes_recv": io.bytes_recv,
    }
