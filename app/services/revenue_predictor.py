"""
app/services/revenue_predictor.py
-----------------------------------
Prediction: Predicted Revenue (next month total, Rs.)
Mirrors legacy notebook 01, but computed live from a shop's real orders
instead of the Instacart dataset.

What: Sums the shop's 30-day forecast (from daily_revenue_forecast.py) to
      get one total-revenue number for next month.
"""

from typing import List, Dict
from app.services.daily_revenue_forecast import compute_daily_forecast

MIN_ORDERS_FOR_ANY_ESTIMATE = 3  # below this we don't guess at all


def predict_next_month_revenue(orders: List[Dict]) -> Dict:
    from app.services.shared import non_cancelled

    if len(non_cancelled(orders)) < MIN_ORDERS_FOR_ANY_ESTIMATE:
        return {
            "status": "no_data",
            "predicted_revenue": None,
            "confidence": "none",
            "message": "Not enough order history to predict next month's revenue.",
        }

    result = compute_daily_forecast(orders)
    if result is None:
        return {
            "status": "no_data",
            "predicted_revenue": None,
            "confidence": "none",
            "message": "Not enough dated order history to predict next month's revenue.",
        }

    predicted_revenue = round(sum(result["forecast"]), 2)
    return {
        "status": "ok",
        "predicted_revenue": predicted_revenue,
        "confidence": result["confidence"],
        "history_days": result["history_days"],
    }