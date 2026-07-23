"""
app/services/daily_revenue_forecast.py
----------------------------------------
Prediction: Daily Revenue Forecast (30-day series)
Mirrors legacy notebook 05, but forecasts from a shop's real order history
instead of the Instacart dataset.

What: Builds a real daily revenue time series for one shop and projects it
      30 days forward.
Why:  This is the single canonical time-series computation for the shop.
      revenue_predictor.py (next-month total) and daily_revenue_avg.py
      (average per day) both import compute_daily_forecast() from here
      instead of re-deriving their own regression — so "Predicted Revenue",
      "Daily Revenue", and the forecast chart can never disagree with each
      other on the dashboard.
Method: Daily bucketing → 7-day rolling mean (smooths order-to-order noise)
        → linear trend (least squares) → clamp implied monthly growth to a
        sane range → rescale the 30-day forecast to match.
"""

from typing import List, Dict, Optional
from app.services.shared import (
    non_cancelled, order_date_range, daily_series, rolling_mean,
    linear_trend, clamp, FORECAST_DAYS, GROWTH_CLAMP_MIN, GROWTH_CLAMP_MAX,
)

MIN_ORDERS_FOR_TREND = 8   # below this, use a flat/naive projection instead of a fitted trend
MIN_DAYS_FOR_TREND = 14    # below this, use a flat/naive projection instead of a fitted trend


def compute_daily_forecast(orders: List[Dict]) -> Optional[Dict]:
    """
    Returns:
        {
          "forecast": [float, ... 30 values],
          "confidence": "low" | "medium" | "high",
          "history_days": int,
          "trailing_avg_daily_revenue": float,
        }
        or None if the shop has no dated order history at all.
    """
    orders = non_cancelled(orders)
    date_range = order_date_range(orders)
    if date_range is None:
        return None

    first_day, last_day, history_days = date_range

    daily_revenue = daily_series(
        orders,
        lambda day_orders: sum(float(o.get("total_amount") or 0) for o in day_orders),
        first_day, last_day,
    )

    trailing_window = daily_revenue[-30:] if daily_revenue else [0.0]
    trailing_avg = sum(trailing_window) / len(trailing_window) if trailing_window else 0.0

    low_confidence = len(orders) < MIN_ORDERS_FOR_TREND or history_days < MIN_DAYS_FOR_TREND

    if low_confidence:
        avg_daily = sum(daily_revenue) / len(daily_revenue) if daily_revenue else 0.0
        forecast = [max(0.0, avg_daily) for _ in range(FORECAST_DAYS)]
        confidence = "low"
    else:
        smoothed = rolling_mean(daily_revenue, 7)
        intercept, slope, r2 = linear_trend(smoothed)
        start_x = len(smoothed)
        raw_forecast = [max(0.0, intercept + slope * (start_x + i)) for i in range(FORECAST_DAYS)]

        predicted_avg = sum(raw_forecast) / len(raw_forecast)
        growth = (predicted_avg - trailing_avg) / trailing_avg if trailing_avg > 0 else 0.0
        growth = clamp(growth, GROWTH_CLAMP_MIN, GROWTH_CLAMP_MAX)
        target_avg = trailing_avg * (1 + growth) if trailing_avg > 0 else predicted_avg

        scale = (target_avg / predicted_avg) if predicted_avg > 0 else 1.0
        forecast = [max(0.0, v * scale) for v in raw_forecast]
        confidence = "high" if r2 >= 0.3 else "medium"

    predicted_avg_daily = sum(forecast) / len(forecast) if forecast else 0.0
    revenue_growth = (
        (predicted_avg_daily - trailing_avg) / trailing_avg
        if trailing_avg > 0 else 0.0
    )

    return {
        "forecast": forecast,
        "confidence": confidence,
        "history_days": history_days,
        "trailing_avg_daily_revenue": trailing_avg,
        "revenue_growth": revenue_growth,  # fraction, e.g. 0.162 == +16.2%
    }


def predict_daily_revenue_forecast(orders: List[Dict]) -> Dict:
    """Public entry point used by the /predictions router — API-ready shape."""
    from datetime import datetime, timedelta, timezone

    result = compute_daily_forecast(orders)
    if result is None:
        return {"status": "no_data", "daily_revenue_forecast": [], "confidence": "none"}

    today = datetime.now(timezone.utc).date()
    forecast = [
        {
            "day": f"Day {i + 1}",
            "date": (today + timedelta(days=i + 1)).isoformat(),
            "revenue": round(v, 2),
        }
        for i, v in enumerate(result["forecast"])
    ]
    return {
        "status": "ok",
        "daily_revenue_forecast": forecast,
        "confidence": result["confidence"],
        "history_days": result["history_days"],
    }