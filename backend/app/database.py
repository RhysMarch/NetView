# database.py
import sqlite3
import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "devices.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the devices table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        mac TEXT PRIMARY KEY,
        ip TEXT,
        online INTEGER,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def get_all_devices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT mac, ip, online, first_seen, last_seen FROM devices")
    rows = cursor.fetchall()
    conn.close()
    return [dict(zip(["mac", "ip", "online", "first_seen", "last_seen"], row)) for row in rows]


def upsert_device(mac, ip):
    now = datetime.datetime.utcnow()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM devices WHERE mac = ?
    """, (mac,))
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
        """, list(exclude_macs))  # <- convert set to list here
    else:
        cursor.execute("UPDATE devices SET online = 0")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database created.")
