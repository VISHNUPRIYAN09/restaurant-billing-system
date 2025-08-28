# utils/calculator.py

from typing import List, Dict

def calc_subtotal(items: List[Dict[str, float]]) -> float:
    """
    Calculate subtotal without GST or discount.
    items: list of dicts [{'price': float, 'qty': int}]
    """
    return round(sum(item['price'] * item['qty'] for item in items), 2)

def calc_gst(subtotal: float, rate: float) -> float:
    """
    Calculate GST based on subtotal.
    rate: GST rate (e.g., 0.05 for 5%)
    """
    return round(subtotal * rate, 2)

def apply_discount(subtotal: float, discount_type: str = "None", discount_value: float = 0.0) -> float:
    """
    Apply discount to subtotal.
    discount_type: "None", "Flat ₹", or "Percentage %"
    """
    if discount_type == "Flat ₹":
        return min(discount_value, subtotal)
    elif discount_type == "Percentage %":
        return round((discount_value / 100) * subtotal, 2)
    return 0.0

def calculate_bill(items: List[Dict[str, float]], gst_rate: float = 0.05,
                   discount_type: str = "None", discount_value: float = 0.0) -> Dict[str, float]:
    """
    Calculate full bill with subtotal, GST, discount, and final total.
    """
    subtotal = calc_subtotal(items)
    gst = calc_gst(subtotal, gst_rate)
    discount = apply_discount(subtotal, discount_type, discount_value)
    total = round(subtotal + gst - discount, 2)

    return {
        "subtotal": subtotal,
        "gst": gst,
        "discount": discount,
        "total": total
    }
