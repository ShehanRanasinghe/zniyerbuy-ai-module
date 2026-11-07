"""
app/routers/trending.py
-----------------------------------
What: Serves trending products and trending categories, computed live
      from recent user_interactions (weighted by action type and
      recency), falling back to all-time engagement metrics when there
      isn't enough recent activity yet.
Why:  Powers the mobile app's "Trending Now" section on Home/Search, via
      the existing Node backend proxy at GET /api/v1/ai/trending/products
      (see backend/src/controllers/ai.controller.js getTrendingProducts)
      and the new GET /api/v1/ai/trending/categories - clients call the
      Node backend, which calls this service, not the other way around.

REPLACES a previous 501 stub - this router was referenced by main.py but
the real implementation had never been written, so GET /trending/ always
returned {"status": "not_implemented"}.

/products' response key is `trending` (not `products`) to match exactly
what ai.controller.js's getTrendingProducts already expects to forward on
(`data.trending || []`).
"""

from fastapi import APIRouter, HTTPException, Query
from app.database import get_products, get_user_interactions
from app.services.trending_engine import get_trending_products, get_trending_categories

router = APIRouter()


@router.get("/products")
def trending_products(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(7, ge=1, le=90, description="How many days back to weigh recent activity"),
):
    """Returns trending products, most-trending-first."""
    try:
        products = get_products()
        interactions = get_user_interactions()
        result = get_trending_products(products, interactions, limit=limit, days=days)
        return {"trending": result, "count": len(result)}
    except Exception as e:
        print(f"Error computing trending products: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute trending products")


@router.get("/categories")
def trending_categories(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(7, ge=1, le=90, description="How many days back to weigh recent activity"),
):
    """Returns trending categories, most-trending-first."""
    try:
        products = get_products()
        interactions = get_user_interactions()
        result = get_trending_categories(products, interactions, limit=limit, days=days)
        return {"categories": result, "count": len(result)}
    except Exception as e:
        print(f"Error computing trending categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute trending categories")