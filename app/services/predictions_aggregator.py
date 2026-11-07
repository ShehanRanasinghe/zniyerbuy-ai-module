"""
app/services/predictions_aggregator.py
------------------------------------------
What: Combines the 6 independent predictor modules into the single
      response shape the seller Analytics page expects.
Why:  Keeps app/routers/predictions.py a thin HTTP layer (matching the
      style of the other routers), while each KPI still lives in its own
      testable file.
"""

from typing import List, Dict
from app.services.shared import non_cancelled
from app.services.revenue_predictor import predict_next_month_revenue
from app.services.daily_revenue_avg import predict_average_daily_revenue
from app.services.daily_revenue_forecast import predict_daily_revenue_forecast
from app.services.user_traffic_predictor import predict_expected_users
from app.services.top_category_classifier import predict_top_category
from app.services.category_sales_prediction import predict_category_sales_response

MIN_ORDERS_FOR_ANY_ESTIMATE = 3


def build_shop_predictions(orders: List[Dict], products: List[Dict]) -> Dict:
    total_orders = len(non_cancelled(orders))

    if total_orders < MIN_ORDERS_FOR_ANY_ESTIMATE:
        return {
            "status": "no_data",
            "message": "Not enough order history yet to generate predictions. "
                       "Predictions unlock once this shop has a few completed orders.",
            "predicted_revenue": None,
            "predicted_revenue_growth_pct": None,
            "predicted_daily_revenue": None,
            "expected_users": None,
            "expected_users_growth_pct": None,
            "top_category": None,
            "top_category_predicted_sales": None,
            "daily_revenue_forecast": [],
            "category_sales_prediction": [],
            "meta": {"total_orders": total_orders, "confidence": "none"},
        }

    revenue = predict_next_month_revenue(orders)
    daily_avg = predict_average_daily_revenue(orders)
    forecast = predict_daily_revenue_forecast(orders)
    users = predict_expected_users(orders)
    top_category = predict_top_category(products)
    categories = predict_category_sales_response(products)

    return {
        "status": "ok",
        "predicted_revenue": revenue["predicted_revenue"],
        "predicted_revenue_growth_pct": revenue["revenue_growth_pct"],
        "predicted_daily_revenue": daily_avg["predicted_daily_revenue"],
        "expected_users": users["expected_users"],
        "expected_users_growth_pct": users["expected_users_growth_pct"],
        "top_category": top_category["top_category"],
        "top_category_predicted_sales": top_category["top_category_predicted_sales"],
        "daily_revenue_forecast": forecast["daily_revenue_forecast"],
        "category_sales_prediction": categories["category_sales_prediction"],
        "meta": {
            "total_orders": total_orders,
            "history_days": forecast.get("history_days"),
            "confidence": forecast.get("confidence"),
            "category_basis": categories.get("category_basis"),
        },
    }