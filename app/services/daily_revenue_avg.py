"""
app/services/daily_revenue_avg.py
------------------------------------
Prediction: Daily Revenue (average per day, Rs.)
Mirrors legacy notebook 02, but computed live from a shop's real orders
instead of the Instacart dataset.

What: Averages the shop's 30-day forecast (from daily_revenue_forecast.py)
      to get one "average per day" number for next month.
"""

from typing import List, Dict
from app.services.daily_revenue_forecast import compute_daily_forecast

MIN_ORDERS_FOR_ANY_ESTIMATE = 3


def predict_average_daily_revenue(orders: List[Dict]) -> Dict:
    from app.services.shared import non_cancelled

    if len(non_cancelled(orders)) < MIN_ORDERS_FOR_ANY_ESTIMATE:
        return {
            "status": "no_data",
            "predicted_daily_revenue": None,
            "confidence": "none",
            "message": "Not enough order history to predict average daily revenue.",
        }

    result = compute_daily_forecast(orders)
    if result is None:
        return {
            "status": "no_data",
            "predicted_daily_revenue": None,
            "confidence": "none",
            "message": "Not enough dated order history to predict average daily revenue.",
        }

    predicted_daily_revenue = round(sum(result["forecast"]) / len(result["forecast"]), 2)
    return {
        "status": "ok",
        "predicted_daily_revenue": predicted_daily_revenue,
        "confidence": result["confidence"],
    }