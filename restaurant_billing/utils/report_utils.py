# utils/report_utils.py

import pandas as pd
from utils.db_utils import get_connection
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime


# ---------------------------
# SALES REPORT (DataFrames)
# ---------------------------
def get_sales_report(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Returns orders between start_date and end_date (YYYY-MM-DD).
    """
    conn = get_connection()
    q = """
    SELECT
      id AS order_id,
      subtotal,
      gst_amount,
      discount_amount,
      total_amount,
      payment_method,
      created_at,
      DATE(created_at) AS date
    FROM orders
    WHERE DATE(created_at) BETWEEN ? AND ?
    ORDER BY created_at DESC
    """
    df = pd.read_sql_query(q, conn, params=[start_date, end_date])
    conn.close()
    return df


def get_top_items(start_date: str, end_date: str, limit: int = 10) -> pd.DataFrame:
    """
    Returns top selling items between start_date and end_date.
    """
    conn = get_connection()
    q = """
    SELECT
      m.name AS item,
      SUM(oi.qty) AS total_qty,
      SUM(oi.line_total) AS revenue
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id
    JOIN menu m   ON m.id = oi.item_id
    WHERE DATE(o.created_at) BETWEEN ? AND ?
    GROUP BY m.name
    ORDER BY total_qty DESC
    LIMIT ?
    """
    df = pd.read_sql_query(q, conn, params=[start_date, end_date, limit])
    conn.close()
    return df


# ---------------------------
# PDF BILL GENERATOR
# ---------------------------
def generate_bill_pdf(order, items, filename="bill.pdf"):
    """
    Generate a simple PDF bill for an order using built-in Helvetica font.
    order: tuple from get_order(order_id)
    items: list of tuples from get_order(order_id)
    """
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 50, "Restaurant Bill")

    # Order details
    c.setFont("Helvetica", 12)
    y = height - 100
    c.drawString(50, y, f"Order ID: {order[0]}")
    y -= 20
    c.drawString(50, y, f"Date: {order[6]}")  # shifted since mode removed

    # Table header
    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Item ID")
    c.drawString(150, y, "Qty")
    c.drawString(220, y, "Unit Price")
    c.drawString(320, y, "Line Total")

    # Table rows
    c.setFont("Helvetica", 12)
    y -= 20
    for item in items:
        c.drawString(50, y, str(item[2]))   # item_id
        c.drawString(150, y, str(item[3]))  # qty
        c.drawString(220, y, f"{item[4]:.2f}")  # unit price
        c.drawString(320, y, f"{item[5]:.2f}")  # line total
        y -= 20
        if y < 100:  # Avoid overflow
            c.showPage()
            y = height - 100

    # Totals
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Subtotal: {order[1]:.2f}")
    y -= 20
    c.drawString(50, y, f"GST: {order[2]:.2f}")
    y -= 20
    c.drawString(50, y, f"Discount: {order[3]:.2f}")
    y -= 20
    c.drawString(50, y, f"Total: {order[4]:.2f}")

    # Footer
    y -= 40
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(200, y, "Thank you for dining with us!")

    c.save()
    return filename


# ---------------------------
# SALES REPORT PDF GENERATOR
# ---------------------------
def generate_sales_report_pdf(start_date: str, end_date: str, filename="sales_report.pdf"):
    """
    Generate a PDF sales report between two dates.
    """
    df = get_sales_report(start_date, end_date)
    top_items = get_top_items(start_date, end_date)

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, height - 50, "Daily Sales Report")

    # Date range
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"From: {start_date} To: {end_date}")
    c.drawString(50, height - 100, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Summary
    total_orders = len(df)
    total_revenue = df['total_amount'].sum() if not df.empty else 0
    c.drawString(50, height - 140, f"Total Orders: {total_orders}")
    c.drawString(250, height - 140, f"Total Revenue: ₹{total_revenue:.2f}")

    # Top Items
    y = height - 180
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Top Selling Items")
    y -= 20
    c.setFont("Helvetica", 12)
    for _, row in top_items.iterrows():
        c.drawString(50, y, f"{row['item']} - Qty: {row['total_qty']} | Revenue: ₹{row['revenue']:.2f}")
        y -= 20
        if y < 100:
            c.showPage()
            y = height - 100

    c.save()
    return filename

