"""
app/services/category_sales_prediction.py
---------------------------------------------
Prediction: Category Sales Prediction (current vs predicted, per category)
Mirrors legacy notebook 06, but computed from a shop's real product catalog
instead of the Instacart dataset's 21 grocery departments.

What: Ranks each of the shop's real categories (Electronics, Fashion,
      Food, Home, etc.) by an engagement score built from views,
      favorites, and recommendation_score, then projects each category's
      product count up or down relative to the shop's average engagement.
Why heuristic, not sales history: there is currently no per-order
      line-item table linking a sale to a specific product/category, so
      real category-level sales can't be computed yet. This is a
      transparent proxy — every response is labeled
      "category_basis": "catalog_engagement_proxy" — and should be
      replaced with a real sales-based model once order line items exist.
"""

from typing import List, Dict
from app.services.shared import clamp

ENGAGEMENT_CLAMP_MIN = -0.30
ENGAGEMENT_CLAMP_MAX = 0.50


def predict_category_sales(products: List[Dict]) -> List[Dict]:
    if not products:
        return []

    stats: Dict[str, Dict] = {}
    for p in products:
        cat = p.get("category") or "Other"
        engagement = (
            float(p.get("views") or 0)
            + float(p.get("favorites_count") or 0) * 2
            + float(p.get("recommendation_score") or 0) * 10
        )
        s = stats.setdefault(cat, {"count": 0, "engagement_sum": 0.0})
        s["count"] += 1
        s["engagement_sum"] += engagement

    for s in stats.values():
        s["avg_engagement"] = s["engagement_sum"] / s["count"] if s["count"] else 0.0

    overall_avg = sum(s["avg_engagement"] for s in stats.values()) / len(stats)

    result = []
    for cat, s in stats.items():
        relative = ((s["avg_engagement"] - overall_avg) / overall_avg) if overall_avg > 0 else 0.0
        relative = clamp(relative, ENGAGEMENT_CLAMP_MIN, ENGAGEMENT_CLAMP_MAX)
        predicted = max(s["count"], round(s["count"] * (1 + relative)))
        result.append({"name": cat, "current": s["count"], "predicted": predicted})

    result.sort(key=lambda r: r["predicted"], reverse=True)
    return result


def predict_category_sales_response(products: List[Dict]) -> Dict:
    """Public entry point used by the /predictions router."""
    categories = predict_category_sales(products)
    if not categories:
        return {
            "status": "no_data",
            "category_sales_prediction": [],
            "message": "No products in the catalog yet.",
        }
    return {
        "status": "ok",
        "category_sales_prediction": categories,
        "category_basis": "catalog_engagement_proxy",
    }