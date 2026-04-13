"""
SwiftClaim Parts Price Database
---------------------------------
SQLite-backed parts pricing database with CRUD operations.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "parts_prices.db")

PARTS_CATALOG = [
    # (part_id, part_name, oem_price, aftermarket_price, labor_hours, labor_rate)
    ("front_bumper",      "Front Bumper",        12000, 7500,  4.0, 800),
    ("rear_bumper",       "Rear Bumper",          10000, 6500,  3.5, 800),
    ("hood",              "Hood",                 22000, 15000, 5.0, 800),
    ("front_left_door",   "Front Left Door",      35000, 24000, 8.0, 800),
    ("front_right_door",  "Front Right Door",     35000, 24000, 8.0, 800),
    ("rear_left_door",    "Rear Left Door",       32000, 21000, 7.5, 800),
    ("rear_right_door",   "Rear Right Door",      32000, 21000, 7.5, 800),
    ("left_headlight",    "Left Headlight",        8500, 4500,  2.5, 800),
    ("right_headlight",   "Right Headlight",       8500, 4500,  2.5, 800),
    ("left_taillight",    "Left Taillight",        7000, 3800,  2.0, 800),
    ("right_taillight",   "Right Taillight",       7000, 3800,  2.0, 800),
    ("windshield",        "Windshield",           18000, 11000, 3.0, 800),
    ("roof",              "Roof",                 55000, 38000, 12.0, 800),
    ("left_fender",       "Left Fender",          14000, 9000,  4.5, 800),
    ("right_fender",      "Right Fender",         14000, 9000,  4.5, 800),
    ("trunk",             "Trunk/Boot Lid",       28000, 18000, 6.0, 800),
]


class PartsDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS parts (
                    part_id          TEXT PRIMARY KEY,
                    part_name        TEXT NOT NULL,
                    oem_price        REAL NOT NULL,
                    aftermarket_price REAL NOT NULL,
                    labor_hours      REAL NOT NULL,
                    labor_rate       REAL NOT NULL,
                    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS claims_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_id    TEXT NOT NULL,
                    part_id     TEXT NOT NULL,
                    severity    TEXT NOT NULL,
                    payout      REAL NOT NULL,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Seed data if empty
            existing = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
            if existing == 0:
                conn.executemany("""
                    INSERT INTO parts
                    (part_id, part_name, oem_price, aftermarket_price, labor_hours, labor_rate)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, PARTS_CATALOG)
            conn.commit()

    def get_part(self, part_id: str) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM parts WHERE part_id = ?", (part_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def get_all_parts(self) -> list:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM parts ORDER BY part_name").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def log_claim(self, claim_id: str, part_id: str, severity: str, payout: float):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO claims_log (claim_id, part_id, severity, payout) VALUES (?,?,?,?)",
                (claim_id, part_id, severity, payout)
            )
            conn.commit()

    def get_claims_log(self) -> list:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM claims_log ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
        return [
            {"id": r[0], "claim_id": r[1], "part_id": r[2],
             "severity": r[3], "payout": r[4], "created_at": r[5]}
            for r in rows
        ]

    def _row_to_dict(self, row) -> dict:
        return {
            "part_id":           row[0],
            "part_name":         row[1],
            "oem_price":         row[2],
            "aftermarket_price": row[3],
            "labor_hours":       row[4],
            "labor_rate":        row[5],
            "labor_cost":        round(row[4] * row[5], 2),
        }
