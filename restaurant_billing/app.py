import os
import streamlit as st
import pandas as pd
from datetime import date

from utils import db_utils
from utils.pdf_utils import generate_bill_pdf
from utils.report_utils import get_sales_report, get_top_items

# ---------------------------
# INIT
# ---------------------------
db_utils.init_db()
st.set_page_config(page_title="Restaurant Billing System", layout="wide")
st.title("🍽 Restaurant Billing System")

# ---------------------------
# BILL SUMMARY CARD
# ---------------------------
def show_bill_summary(bill):
    st.markdown("""
        <style>
        .bill-card {
            background-color: #1e1e1e;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0px 0px 10px rgba(0,0,0,0.3);
            margin-top: 10px;
            color: white;
        }
        .bill-row {
            display: flex;
            justify-content: space-between;
            font-size: 16px;
            padding: 4px 0;
        }
        .bill-total {
            font-weight: bold;
            font-size: 18px;
            color: #00ff99;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="bill-card">
            <div class="bill-row"><span>Subtotal:</span><span>₹ {bill.get('subtotal', 0):.2f}</span></div>
            <div class="bill-row"><span>GST:</span><span>₹ {bill.get('gst', bill.get('gst_amount', 0)):.2f}</span></div>
            <div class="bill-row"><span>Discount:</span><span>₹ {bill.get('discount', bill.get('discount_amount', 0)):.2f}</span></div>
            <hr>
            <div class="bill-row bill-total"><span>Total:</span><span>₹ {bill.get('total', bill.get('total_amount', 0)):.2f}</span></div>
        </div>
    """, unsafe_allow_html=True)

# ---------------------------
# MENU UPLOAD + DISPLAY
# ---------------------------
with st.expander("📂 Upload / Refresh Menu"):
    uploaded_file = st.file_uploader(
        "Upload a CSV file for Menu (columns: name,category,price,gst_percent)",
        type=["csv"]
    )
    if uploaded_file is not None:
        df_up = pd.read_csv(uploaded_file)
        df_up.to_csv("data/menu.csv", index=False)
        db_utils.insert_menu_items_from_csv("data/menu.csv")
        st.success("✅ Menu updated!")

conn = db_utils.get_connection()
menu_df = pd.read_sql("SELECT * FROM menu", conn)
conn.close()

st.subheader("Menu")
st.dataframe(menu_df, use_container_width=True)

# ---------------------------
# TABS: Billing | Reports
# ---------------------------
tab1, tab2 = st.tabs(["🧾 Billing", "📊 Reports"])

# ---------------- BILLING TAB ----------------
with tab1:
    st.subheader("Start New Order")
    mode = st.radio("Select Order Mode", ["DINE_IN", "TAKEAWAY"], horizontal=True)

    if st.button("Begin Order"):
        order_id = db_utils.begin_order(mode)
        st.session_state["order_id"] = order_id
        st.success(f"✅ New Order Started (ID: {order_id})")

    if "order_id" in st.session_state:
        order_id = st.session_state["order_id"]
        st.markdown(f"### Active Order ID: *{order_id}*")

        # Add Items
        colA, colB, colC = st.columns([2, 1, 1])
        with colA:
            item_id = st.number_input("Item ID", min_value=1, step=1)
        with colB:
            qty = st.number_input("Qty", min_value=1, step=1)
        with colC:
            if st.button("Add Item"):
                try:
                    db_utils.add_item(order_id, item_id, qty)
                    st.success("Item added ✅")
                except Exception as e:
                    st.error(f"Error: {e}")

        # Show current items
        conn = db_utils.get_connection()
        items_df = pd.read_sql(f"SELECT * FROM order_items WHERE order_id={order_id}", conn)
        conn.close()

        st.write("### Current Order Items")
        st.dataframe(items_df, use_container_width=True)

        # Totals and Payment Info
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            discount = st.number_input("Discount (₹)", min_value=0.0, step=1.0)
        with col2:
            gst_rate = st.slider("GST Rate", 0.0, 0.28, 0.05)
        with col3:
            pay_method = st.selectbox("Payment Method", ["CASH", "CARD", "UPI"])

        # Compute Bill
        if st.button("Compute Bill"):
            breakdown = db_utils.compute_totals(order_id, discount, gst_rate)
            st.session_state["breakdown"] = breakdown
            st.success("Bill computed ✅")
            show_bill_summary(breakdown)

        # Finalize Order or Generate PDF
        colF1, colF2 = st.columns(2)
        with colF1:
            if st.button("Finalize Order"):
                db_utils.finalize_order(order_id, pay_method)
                st.success(f"Order {order_id} finalized with {pay_method} ✅")

        with colF2:
            if st.button("Generate PDF Bill"):
                try:
                    conn = db_utils.get_connection()

                    # Get order and items
                    order_row = pd.read_sql(f"SELECT * FROM orders WHERE id={order_id}", conn).iloc[0].to_dict()
                    items = pd.read_sql(f"""
                        SELECT m.name, oi.qty, oi.unit_price, oi.line_total
                        FROM order_items oi
                        JOIN menu m ON m.id = oi.item_id
                        WHERE oi.order_id={order_id}
                    """, conn).to_dict(orient="records")
                    conn.close()

                    # Rebuild item list for PDF
                    items_for_pdf = [
                        {
                            "name": row["name"],
                            "qty": int(row["qty"]),
                            "unit_price": float(row["unit_price"]),
                            "line_total": float(row["line_total"]),
                        } for row in items
                    ]

                    # Add financials from computed bill
                    breakdown = st.session_state.get("breakdown", {})
                    order_row.update({
                        "subtotal": breakdown.get("subtotal", 0),
                        "gst_amount": breakdown.get("gst", 0),
                        "discount_amount": breakdown.get("discount", 0),
                        "total_amount": breakdown.get("total", 0),
                        "payment_method": pay_method
                    })

                    # Generate and download PDF
                    pdf_path = generate_bill_pdf(order_row, items_for_pdf)
                    st.success(f"PDF generated successfully!")
                    with open(pdf_path, "rb") as f:
                        st.download_button("⬇ Download Bill PDF", f, file_name=os.path.basename(pdf_path))

                except Exception as e:
                    st.error(f"PDF error: {e}")

        if st.button("Clear Active Order"):
            st.session_state.pop("order_id")
            st.info("Active order cleared.")

# ---------------- REPORTS TAB ----------------
with tab2:
    st.subheader("Sales Reports")
    today = date.today()
    d_range = st.date_input("Select date range", value=(today, today))

    if isinstance(d_range, tuple):
        start_dt, end_dt = d_range
    else:
        start_dt = end_dt = d_range

    start_s = start_dt.strftime("%Y-%m-%d")
    end_s = end_dt.strftime("%Y-%m-%d")

    if st.button("Generate Report"):
        # Orders
        sales_df = get_sales_report(start_s, end_s)
        st.write("### Orders")
        st.dataframe(sales_df, use_container_width=True)

        csv_data = sales_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download Sales CSV",
            data=csv_data,
            file_name=f"sales_{start_s}to{end_s}.csv",
            mime="text/csv"
        )

        # Top Items
        top_df = get_top_items(start_s, end_s, limit=10)
        st.write("### Top Items")
        st.dataframe(top_df, use_container_width=True)

        top_csv = top_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download Top Items CSV",
            data=top_csv,
            file_name=f"top_items_{start_s}to{end_s}.csv",
            mime="text/csv"
        )