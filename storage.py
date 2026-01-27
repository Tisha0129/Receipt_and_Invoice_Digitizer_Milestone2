import sqlite3
import hashlib

DB_NAME = "receipts.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def receipt_exists_by_raw_text(raw_text):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM receipts WHERE raw_text = ? LIMIT 1",
        (raw_text,)
    )
    exists = cur.fetchone() is not None

    conn.close()
    return exists

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        merchant TEXT,
        date TEXT,
        total TEXT,
        tax TEXT,
        raw_text TEXT
    )
    """)

    cur.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER,
    name TEXT,
    quantity INTEGER,
    price REAL,
    FOREIGN KEY (receipt_id) REFERENCES receipts(id)
)
""")


    conn.commit()
    conn.close()


def insert_receipt(data, raw_text):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO receipts (merchant, date, total, tax, raw_text)
    VALUES (?, ?, ?, ?, ?)
    """, (
        data["vendor"],
        data["date"],
        data["total"],
        data["tax"],
        raw_text
    ))

    receipt_id = cur.lastrowid

    for item in data["line_items"]:
        cur.execute("""
            INSERT INTO items (receipt_id, name, quantity, price)
            VALUES (?, ?, ?, ?)
            """, (
                receipt_id,               
                item["name"],
                item["quantity"],
                item["price"]
            ))



    conn.commit()
    conn.close()


def fetch_receipts():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, merchant, date, total, tax FROM receipts ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_receipt_items(receipt_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, quantity, price
        FROM items
        WHERE receipt_id = ?
    """, (receipt_id,))
    rows = cur.fetchall()
    conn.close()
    return rows
    
