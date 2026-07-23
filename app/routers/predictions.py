"""
app/routers/predictions.py
---------------------------
What: Serves live, per-shop AI predictions for the seller Analytics page.
Why:  Pulls this shop's real orders + products from Supabase on every
      request and computes fresh numbers via the 6 predictor modules
      in app/services/.
"""

from fastapi import APIRouter, HTTPException
from app.database import get_orders_by_shop, get_products_by_shop
from app.services.predictions_aggregator import build_shop_predictions

router = APIRouter()


@router.get("/shop/{shop_id}")
def get_shop_predictions(shop_id: str):
    """Returns next-month predictions for a single shop, computed live."""
    try:
        orders = get_orders_by_shop(shop_id)
        products = get_products_by_shop(shop_id)

        if orders is None or products is None:
            raise HTTPException(status_code=503, detail="Could not reach the database")

        result = build_shop_predictions(orders, products)
        result["shop_id"] = shop_id
        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating predictions for shop {shop_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate predictions")