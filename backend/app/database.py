# NetView/backend/app/database.py

import sqlite3
import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "devices.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # devices table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        mac TEXT PRIMARY KEY,
        ip TEXT,
        online INTEGER,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP
    )
    """)

    # name column
    cursor.execute("PRAGMA table_info(devices)")
    cols = [r[1] for r in cursor.fetchall()]
    if "name" not in cols:
        cursor.execute("ALTER TABLE devices ADD COLUMN name TEXT")

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
    # use timezone-aware UTC now
    now = datetime.datetime.now(datetime.timezone.utc)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE devices
        SET name = ?
        WHERE mac = ?
    """, (new_name or None, mac))
    conn.commit()
    conn.close()


# alerts helpers

def add_alert(type: str, mac: str, ip: str, message: str):
    now = datetime.datetime.now(datetime.timezone.utc)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check for similar recent alert in the last 5 seconds
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
        return  # Skip inserting duplicate alert

    # Insert the new alert
    cursor.execute("""
        INSERT INTO alerts (type, mac, ip, timestamp, message)
        VALUES (?, ?, ?, ?, ?)
    """, (type, mac, ip, now, message))

    # Retain only the most recent 100 alerts
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
    conn = sqlite3.connect(DB_PATH)
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
    print("Database migrated/created.")
