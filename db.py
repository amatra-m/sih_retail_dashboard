from pathlib import Path
import sqlite3
from datetime import datetime

DB_PATH = Path(__file__).with_name("store.db")

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def connect():
    con = sqlite3.connect(DB_PATH, timeout=5, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    return con

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            footfall INTEGER NOT NULL DEFAULT 0,
            customers_inside INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS inventory (
            product TEXT PRIMARY KEY,
            shelf TEXT NOT NULL,
            stock_percent REAL NOT NULL,
            status TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS queues (
            counter TEXT PRIMARY KEY,
            people INTEGER NOT NULL DEFAULT 0,
            wait_min REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'NORMAL',
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS trolleys (
            trolley_id TEXT PRIMARY KEY,
            items INTEGER NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            recommendation TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            severity TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS heatmap_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            x REAL NOT NULL,
            y REAL NOT NULL,
            zone TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS footfall_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_label TEXT NOT NULL,
            count INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            peak_window TEXT,
            expected_footfall INTEGER,
            crowd_level TEXT,
            updated_at TEXT
        );
        """)

def seed_demo():
    init_db()
    with connect() as con:
        con.execute("""
            INSERT OR IGNORE INTO metrics(id, footfall, customers_inside, updated_at)
            VALUES(1, 327, 42, ?)
        """, (now(),))

        inventory = [
            ("Coke 500 ml", "A1", 20, "CRITICAL", now()),
            ("Lays Classic", "A2", 72, "HEALTHY", now()),
            ("Maggi", "B1", 38, "LOW", now()),
            ("Pepsi 500 ml", "B2", 86, "HEALTHY", now()),
        ]
        con.executemany("""
            INSERT OR IGNORE INTO inventory(product, shelf, stock_percent, status, updated_at)
            VALUES(?,?,?,?,?)
        """, inventory)

        queues = [
            ("Counter 1", 3, 2.0, "NORMAL", now()),
            ("Counter 2", 7, 4.5, "CONGESTED", now()),
            ("Counter 3", 2, 1.4, "NORMAL", now()),
        ]
        con.executemany("""
            INSERT OR IGNORE INTO queues(counter, people, wait_min, status, updated_at)
            VALUES(?,?,?,?,?)
        """, queues)

        trolleys = [
            ("T01", 8, 620, "Counter 3", now()),
            ("T02", 14, 1130, "Counter 1", now()),
        ]
        con.executemany("""
            INSERT OR IGNORE INTO trolleys(trolley_id, items, total, recommendation, updated_at)
            VALUES(?,?,?,?,?)
        """, trolleys)

        if con.execute("SELECT COUNT(*) FROM alerts").fetchone()[0] == 0:
            con.executemany("""
                INSERT INTO alerts(severity, category, location, message, created_at)
                VALUES(?,?,?,?,?)
            """, [
                ("critical", "inventory", "Shelf A1", "Coke at 20% — refill now", now()),
                ("warning", "queue", "Counter 2", "Queue congested — open/route to another counter", now()),
                ("warning", "planogram", "Shelf B1", "Possible product misalignment detected", now()),
            ])

        if con.execute("SELECT COUNT(*) FROM heatmap_points").fetchone()[0] == 0:
            pts = [
                (0.15,0.20,"Entrance"), (0.18,0.22,"Entrance"), (0.21,0.24,"Entrance"),
                (0.43,0.36,"Snacks"), (0.46,0.38,"Snacks"), (0.48,0.41,"Snacks"),
                (0.52,0.44,"Snacks"), (0.55,0.45,"Snacks"), (0.57,0.47,"Snacks"),
                (0.75,0.72,"Checkout"), (0.78,0.75,"Checkout"), (0.80,0.77,"Checkout"),
                (0.82,0.74,"Checkout"), (0.77,0.79,"Checkout"),
            ]
            con.executemany("""
                INSERT INTO heatmap_points(x,y,zone,created_at)
                VALUES(?,?,?,?)
            """, [(x,y,z,now()) for x,y,z in pts])

        if con.execute("SELECT COUNT(*) FROM footfall_history").fetchone()[0] == 0:
            hist = [("09:00",25),("10:00",38),("11:00",52),("12:00",71),
                    ("13:00",64),("14:00",58),("15:00",73),("16:00",88)]
            con.executemany("""
                INSERT INTO footfall_history(time_label,count,created_at)
                VALUES(?,?,?)
            """, [(t,c,now()) for t,c in hist])

        con.execute("""
            INSERT OR IGNORE INTO predictions(id,peak_window,expected_footfall,crowd_level,updated_at)
            VALUES(1,'17:00–18:00',95,'HIGH',?)
        """, (now(),))

def add_alert(severity, category, location, message):
    with connect() as con:
        con.execute("""
            INSERT INTO alerts(severity,category,location,message,created_at)
            VALUES(?,?,?,?,?)
        """, (severity, category, location, message, now()))

def upsert_inventory(product, shelf, stock_percent):
    stock_percent = max(0, min(100, float(stock_percent)))
    status = "CRITICAL" if stock_percent <= 20 else "LOW" if stock_percent <= 40 else "HEALTHY"
    with connect() as con:
        con.execute("""
            INSERT INTO inventory(product,shelf,stock_percent,status,updated_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(product) DO UPDATE SET
                shelf=excluded.shelf,
                stock_percent=excluded.stock_percent,
                status=excluded.status,
                updated_at=excluded.updated_at
        """, (product, shelf, stock_percent, status, now()))

def upsert_queue(counter, people, wait_min=None):
    people = int(people)
    if wait_min is None:
        wait_min = round(people * 0.7, 1)
    status = "CONGESTED" if people >= 6 else "BUSY" if people >= 4 else "NORMAL"
    with connect() as con:
        con.execute("""
            INSERT INTO queues(counter,people,wait_min,status,updated_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(counter) DO UPDATE SET
                people=excluded.people,
                wait_min=excluded.wait_min,
                status=excluded.status,
                updated_at=excluded.updated_at
        """, (counter, people, float(wait_min), status, now()))

def upsert_trolley(trolley_id, items, total, recommendation=""):
    with connect() as con:
        con.execute("""
            INSERT INTO trolleys(trolley_id,items,total,recommendation,updated_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(trolley_id) DO UPDATE SET
                items=excluded.items,
                total=excluded.total,
                recommendation=excluded.recommendation,
                updated_at=excluded.updated_at
        """, (trolley_id, int(items), float(total), recommendation, now()))

def update_footfall(footfall, customers_inside):
    with connect() as con:
        con.execute("""
            INSERT INTO metrics(id,footfall,customers_inside,updated_at)
            VALUES(1,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                footfall=excluded.footfall,
                customers_inside=excluded.customers_inside,
                updated_at=excluded.updated_at
        """, (int(footfall), int(customers_inside), now()))

def add_heatmap_point(x, y, zone=""):
    with connect() as con:
        con.execute("""
            INSERT INTO heatmap_points(x,y,zone,created_at)
            VALUES(?,?,?,?)
        """, (float(x), float(y), zone, now()))
