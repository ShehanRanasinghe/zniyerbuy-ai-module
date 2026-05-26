from fastapi import APIRouter
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

router = APIRouter()

# Mock sales data (will be replaced with Supabase data in task 7.2)
sales_data = {
    "Samba Rice 5kg": [120, 135, 110, 150, 165, 180],
    "Ceylon Pepper 100g": [45, 50, 40, 55, 60, 58],
    "Green Tomatoes 1kg": [200, 180, 220, 195, 210, 230],
    "Anchor Milk Powder 400g": [80, 85, 75, 90, 95, 100],
    "Kurakkan Flour 1kg": [60, 65, 55, 70, 75, 80],
    "Coconut Oil 500ml": [90, 95, 85, 100, 110, 115],
    "Dhal 1kg": [150, 160, 140, 170, 175, 185],
    "Gotukola Bundles": [300, 280, 320, 295, 310, 330],
}

months = ["Nov", "Dec", "Jan", "Feb", "Mar", "Apr"]

def predict_next_month(sales: list):
    x = np.array(range(len(sales))).reshape(-1, 1)
    y = np.array(sales)
    model = LinearRegression()
    model.fit(x, y)
    next_month = np.array([[len(sales)]])
    prediction = model.predict(next_month)[0]
    return round(float(prediction))

@router.get("/predict")
def get_demand_prediction(product: str = None):
    try:
        if product and product in sales_data:
            sales = sales_data[product]
            prediction = predict_next_month(sales)
            trend = "↑ increasing" if prediction > sales[-1] else "↓ decreasing"
            return {
                "product": product,
                "historical_sales": dict(zip(months, sales)),
                "predicted_next_month": prediction,
                "trend": trend
            }

        # Return predictions for all products
        predictions = []
        for name, sales in sales_data.items():
            prediction = predict_next_month(sales)
            trend = "↑ increasing" if prediction > sales[-1] else "↓ decreasing"
            predictions.append({
                "product": name,
                "current_month_sales": sales[-1],
                "predicted_next_month": prediction,
                "trend": trend
            })

        predictions.sort(key=lambda x: x["predicted_next_month"], reverse=True)

        return {
            "predictions": predictions,
            "model": "linear_regression",
            "based_on_months": months
        }

    except Exception as e:
        return {"error": str(e)}