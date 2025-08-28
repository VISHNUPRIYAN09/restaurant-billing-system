import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime


def generate_bill_pdf(order, items, save_dir="bills"):
    """
    Generate a bill PDF for a given order.

    Args:
        order (dict): Order details (id, mode, subtotal, gst_amount, 
                      discount_amount, total_amount, payment_method, created_at).
        items (list of dict): Items (name, qty, unit_price, line_total).
        save_dir (str): Directory to save PDF.

    Returns:
        str: Absolute path to saved PDF file.
    """
    os.makedirs(save_dir, exist_ok=True)

    # Use order ID or fallback to timestamp
    order_id = order.get("id") or datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"bill_{order_id}.pdf"
    filepath = os.path.abspath(os.path.join(save_dir, filename))

    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # HEADER
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 50, "🍽 Restaurant Bill")

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, f"Bill No: {order_id}")
    c.drawRightString(width - 50, height - 80,
                      f"Date: {order.get('created_at') or datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # ITEM TABLE HEADERS
    y = height - 120
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Item")
    c.drawString(250, y, "Qty")
    c.drawString(300, y, "Price")
    c.drawString(380, y, "Line Total")

    y -= 20
    c.setFont("Helvetica", 10)

    # ITEMS LOOP
    for item in items:
        name = str(item.get("name", "Unknown"))
        qty = int(item.get("qty", 0))
        line_total = float(item.get("line_total", 0.0))
        unit_price = float(item.get("unit_price", (line_total / qty if qty else 0.0)))

        c.drawString(50, y, name)
        c.drawString(250, y, str(qty))
        c.drawString(300, y, f"{unit_price:.2f}")
        c.drawString(380, y, f"{line_total:.2f}")
        y -= 20

        # Handle page overflow
        if y < 150:
            c.showPage()
            y = height - 100
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, "Item")
            c.drawString(250, y, "Qty")
            c.drawString(300, y, "Price")
            c.drawString(380, y, "Line Total")
            y -= 20
            c.setFont("Helvetica", 10)

    # TOTALS
    subtotal = float(order.get("subtotal", 0.0))
    gst = float(order.get("gst_amount", 0.0))
    discount = float(order.get("discount_amount", 0.0))
    total = float(order.get("total_amount", subtotal + gst - discount))

    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 50, y, f"Subtotal: ₹{subtotal:.2f}")

    y -= 15
    c.drawRightString(width - 50, y, f"GST: ₹{gst:.2f}")

    y -= 15
    c.drawRightString(width - 50, y, f"Discount: -₹{discount:.2f}")

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 50, y, f"Total: ₹{total:.2f}")

    # FOOTER
    y -= 40
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Payment Method: {order.get('payment_method', 'N/A')}")
    c.drawString(50, y - 15, f"Order Mode: {order.get('mode', 'N/A')}")
    c.drawString(50, y - 30, "🙏 Thank you! Visit again.")

    c.save()
    return filepath 