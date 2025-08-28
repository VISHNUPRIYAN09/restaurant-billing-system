# utils/db_utils.py

import sqlite3
import os
import pandas as pd
from datetime import datetime

DB_PATH = "db/restaurant.db"

# ---------------------------
# CONNECTION
# ---------------------------
def get_connection():
    """Return a new SQLite DB connection"""
    return sqlite3.connect(DB_PATH)

# ---------------------------
# INIT DATABASE
# ---------------------------
def init_db(reset: bool = False):
    """
    Create database and tables if not exists.
    Use reset=True to drop and recreate all tables.
    """
    if not os.path.exists("db"):
        os.makedirs("db")

    conn = get_connection()
    cur = conn.cursor()

    if reset:
        cur.executescript("""
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS order_items;
            DROP TABLE IF EXISTS menu;
        """)

    # Menu table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            gst_percent REAL DEFAULT 0.05
        )
    """)

    # Orders table (standardized names)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode TEXT,
            subtotal REAL,
            gst_amount REAL,
            discount_amount REAL,
            total_amount REAL,
            payment_method TEXT,
            created_at TEXT
        )
    """)

    # Order Items table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            item_id INTEGER,
            qty INTEGER,
            unit_price REAL,
            line_total REAL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(item_id) REFERENCES menu(id)
        )
    """)

    conn.commit()
    conn.close()

# ---------------------------
# MENU
# ---------------------------
def insert_menu_items_from_csv(csv_path):
    """Load menu items from CSV into database"""
    df = pd.read_csv(csv_path)
    conn = get_connection()
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO menu (name, category, price, gst_percent)
            VALUES (?, ?, ?, ?)
        """, (row["name"], row["category"], row["price"], row.get("gst_percent", 0.05)))
    conn.commit()
    conn.close()

# ---------------------------
# ORDER FLOW
# ---------------------------
def begin_order(mode="DINE_IN"):
    """Start new order and return order_id"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (mode, subtotal, gst_amount, discount_amount, total_amount, payment_method, created_at)
        VALUES (?, 0, 0, 0, 0, 'PENDING', ?)
    """, (mode, datetime.now().isoformat()))
    conn.commit()
    order_id = cur.lastrowid
    conn.close()
    return order_id

def add_item(order_id, item_id, qty):
    """Add item to order"""
    conn = get_connection()
    cur = conn.cursor()

    # Fetch item price
    cur.execute("SELECT price FROM menu WHERE id=?", (item_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("Item not found")

    unit_price = row[0]
    line_total = unit_price * qty

    cur.execute("""
        INSERT INTO order_items (order_id, item_id, qty, unit_price, line_total)
        VALUES (?, ?, ?, ?, ?)
    """, (order_id, item_id, qty, unit_price, line_total))

    conn.commit()
    conn.close()

# ---------------------------
# BILLING
# ---------------------------
def compute_totals(order_id, discount=0.0, gst_rate=0.05):
    """Compute subtotal, gst, discount, total"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT SUM(line_total) FROM order_items WHERE order_id=?", (order_id,))
    subtotal = cur.fetchone()[0] or 0.0

    gst_amount = subtotal * gst_rate
    total_amount = subtotal + gst_amount - discount

    cur.execute("""
        UPDATE orders SET subtotal=?, gst_amount=?, discount_amount=?, total_amount=?
        WHERE id=?
    """, (subtotal, gst_amount, discount, total_amount, order_id))

    conn.commit()
    conn.close()

    return {
        "subtotal": subtotal,
        "gst_amount": gst_amount,
        "discount_amount": discount,
        "total_amount": total_amount
    }

def finalize_order(order_id, payment_method):
    """Finalize and save payment method"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET payment_method=? WHERE id=?", (payment_method, order_id))
    conn.commit()
    conn.close()



  