# reset_db.py

from utils import db_utils

if __name__ == "__main__":
    print("Resetting database...")
    db_utils.init_db(reset=True)

    # --- Insert sample menu items ---
    sample_items = [
        ("Margherita Pizza", "Food", 120.0, 0.05),
        ("Veg Burger", "Food", 80.0, 0.05),
        ("French Fries", "Snacks", 60.0, 0.05),
        ("Cold Coffee", "Beverages", 50.0, 0.05),
        ("Coca Cola", "Beverages", 40.0, 0.05),
    ]

    conn = db_utils.get_connection()
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO menu (name, category, price, gst_percent)
        VALUES (?, ?, ?, ?)
    """, sample_items)
    conn.commit()
    conn.close()

    print("✅ Database reset complete!")
    print("✅ Sample menu items added successfully!")


