# backend/app/database.py

import sqlite3
import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "devices.db")


def _get_conn():
    """
    Create a SQLite connection with:
     - WAL journal mode (better concurrent reads/writes)
     - busy timeout of 5s before “database is locked” error
     - thread‐safety disabled check so you can share across threads
    """
    conn = sqlite3.connect(
        DB_PATH,
        timeout=5.0,
        check_same_thread=False,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    # ensure our busy timeout
    conn.execute("PRAGMA busy_timeout = 5000;")
    # ensure WAL journaling
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db():
    conn = _get_conn()
    cursor = conn.cursor()

    # devices table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        mac TEXT PRIMARY KEY,
        ip TEXT,
        online INTEGER,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP,
        name TEXT,
        hostname TEXT,
        vendor TEXT
    )
    """)

    # alerts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        mac TEXT,
        ip TEXT,
        timestamp TIMESTAMP,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_all_devices():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mac, ip, online, first_seen, last_seen, name, hostname, vendor
        FROM devices
    """)
    rows = cursor.fetchall()
    conn.close()

    keys = ["mac", "ip", "online", "first_seen", "last_seen", "name", "hostname", "vendor"]
    return [dict(zip(keys, row)) for row in rows]


def upsert_device(mac, ip, hostname=None, vendor=None):
    now = datetime.datetime.now(datetime.timezone.utc)
    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM devices WHERE mac = ?", (mac,))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("""
            UPDATE devices
            SET ip        = ?,
                online    = 1,
                last_seen = ?,
                hostname  = COALESCE(?, hostname),
                vendor    = COALESCE(?, vendor)
            WHERE mac = ?
        """, (ip, now, hostname, vendor, mac))
    else:
        cursor.execute("""
            INSERT INTO devices (
                mac, ip, online,
                first_seen, last_seen,
                hostname, vendor
            ) VALUES (?, ?, 1, ?, ?, ?, ?)
        """, (mac, ip, now, now, hostname, vendor))

    conn.commit()
    conn.close()


def mark_offline(online_macs: set[str]):
    conn = _get_conn()
    cursor = conn.cursor()

    # Step 1: Mark everything offline
    cursor.execute("UPDATE devices SET online = 0")

    # Step 2: Mark only known MACs back online
    if online_macs:
        cursor.executemany(
            "UPDATE devices SET online = 1 WHERE mac = ?",
            [(mac,) for mac in online_macs if mac]
        )

    conn.commit()
    conn.close()


def rename_device(mac: str, new_name: str):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE devices
        SET name = ?
        WHERE mac = ?
    """, (new_name or None, mac))
    conn.commit()
    conn.close()


def add_alert(type: str, mac: str, ip: str, message: str):
    now = datetime.datetime.now(datetime.timezone.utc)
    conn = _get_conn()
    cursor = conn.cursor()

    # Dedupe any alert of the same type+mac+message in the last 5s
    cursor.execute("""
        SELECT 1 FROM alerts
        WHERE type = ?
          AND mac = ?
          AND message = ?
          AND timestamp > datetime(?, '-5 seconds')
        LIMIT 1
    """, (type, mac, message, now.isoformat()))
    if cursor.fetchone():
        conn.close()
        return

    cursor.execute("""
        INSERT INTO alerts (type, mac, ip, timestamp, message)
        VALUES (?, ?, ?, ?, ?)
    """, (type, mac, ip, now, message))

    # keep only most recent 100
    cursor.execute("""
        DELETE FROM alerts
        WHERE id NOT IN (
            SELECT id FROM alerts
            ORDER BY timestamp DESC
            LIMIT 100
        )
    """)
    conn.commit()
    conn.close()


def get_alerts():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, type, mac, ip, timestamp, message
        FROM alerts
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    keys = ["id", "type", "mac", "ip", "timestamp", "message"]
    return [dict(zip(keys, row)) for row in rows]


if __name__ == "__main__":
    init_db()
    print("Database initialized with WAL mode and busy timeout.")
