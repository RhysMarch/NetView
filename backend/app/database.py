# database.py
import sqlite3
import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "devices.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1) Create the devices table if missing
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        mac TEXT PRIMARY KEY,
        ip TEXT,
        online INTEGER,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP
    )
    """)

    # 2) Ensure `name` column exists (migrate if needed)
    cursor.execute("PRAGMA table_info(devices)")
    cols = [r[1] for r in cursor.fetchall()]
    if "name" not in cols:
        cursor.execute("ALTER TABLE devices ADD COLUMN name TEXT")

    conn.commit()
    conn.close()


def get_all_devices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mac, ip, online, first_seen, last_seen, name
        FROM devices
    """)
    rows = cursor.fetchall()
    conn.close()

    keys = ["mac", "ip", "online", "first_seen", "last_seen", "name"]
    return [dict(zip(keys, row)) for row in rows]


def upsert_device(mac, ip):
    now = datetime.datetime.utcnow()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM devices WHERE mac = ?", (mac,))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("""
            UPDATE devices
            SET ip = ?, online = 1, last_seen = ?
            WHERE mac = ?
        """, (ip, now, mac))
    else:
        cursor.execute("""
            INSERT INTO devices (mac, ip, online, first_seen, last_seen)
            VALUES (?, ?, 1, ?, ?)
        """, (mac, ip, now, now))

    conn.commit()
    conn.close()


def mark_offline(exclude_macs):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if exclude_macs:
        placeholders = ",".join("?" for _ in exclude_macs)
        cursor.execute(f"""
            UPDATE devices SET online = 0
            WHERE mac NOT IN ({placeholders})
        """, list(exclude_macs))
    else:
        cursor.execute("UPDATE devices SET online = 0")

    conn.commit()
    conn.close()


def rename_device(mac: str, new_name: str):
    """Set or clear the human‐friendly name for a device."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE devices
        SET name = ?
        WHERE mac = ?
    """, (new_name or None, mac))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database migrated/created.")
