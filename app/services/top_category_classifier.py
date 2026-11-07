"""
app/services/top_category_classifier.py
-------------------------------------------
Prediction: Next Month Top Category
Mirrors legacy notebook 04, but computed from a shop's real product catalog
instead of the Instacart department classifier.

What: Picks the #1 category from category_sales_prediction.py.
"""

from typing import List, Dict
from app.services.category_sales_prediction import predict_category_sales


def predict_top_category(products: List[Dict]) -> Dict:
    categories = predict_category_sales(products)
    if not categories:
        return {
            "status": "no_data",
            "top_category": None,
            "top_category_predicted_sales": None,
            "message": "No products in the catalog yet.",
        }

    top = categories[0]
    return {
        "status": "ok",
        "top_category": top["name"],
        "top_category_predicted_sales": top["predicted"],
    }