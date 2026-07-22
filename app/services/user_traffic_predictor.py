"""
app/services/user_traffic_predictor.py
-----------------------------------------
Prediction: Expected Users (distinct customers next month)
Mirrors legacy notebook 03, but computed live from a shop's real orders
instead of the Instacart dataset.

What: Counts distinct customers (by phone, falling back to name) in the
      trailing 30 days, compares to the 30 days before that, and projects
      the growth rate forward — clamped to a sane range.
"""

from datetime import timedelta
from typing import List, Dict
from app.services.shared import non_cancelled, order_date_range, customer_id, clamp, GROWTH_CLAMP_MIN, GROWTH_CLAMP_MAX, parse_dt

MIN_ORDERS_FOR_ANY_ESTIMATE = 3


def predict_expected_users(orders: List[Dict]) -> Dict:
    filtered = non_cancelled(orders)

    if len(filtered) < MIN_ORDERS_FOR_ANY_ESTIMATE:
        return {
            "status": "no_data",
            "expected_users": None,
            "message": "Not enough order history to predict expected users.",
        }

    date_range = order_date_range(filtered)
    if date_range is None:
        return {
            "status": "no_data",
            "expected_users": None,
            "message": "Not enough dated order history to predict expected users.",
        }

    first_day, last_day, _ = date_range
    window_start = max(first_day, last_day - timedelta(days=29))

    trailing_orders = [
        o for o in filtered
        if window_start <= parse_dt(o.get("created_at")).date() <= last_day
    ]
    prev_window_start = window_start - timedelta(days=30)
    prev_window_end = window_start - timedelta(days=1)
    prev_orders = [
        o for o in filtered
        if prev_window_start <= parse_dt(o.get("created_at")).date() <= prev_window_end
    ]

    trailing_customers = len({customer_id(o) for o in trailing_orders})
    prev_customers = len({customer_id(o) for o in prev_orders})

    if prev_customers > 0:
        growth = (trailing_customers - prev_customers) / prev_customers
        growth = clamp(growth, GROWTH_CLAMP_MIN, GROWTH_CLAMP_MAX)
    else:
        growth = 0.0

    expected = round(trailing_customers * (1 + growth))
    expected = max(expected, trailing_customers, 0)

    return {"status": "ok", "expected_users": expected}