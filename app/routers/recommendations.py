"""
app/routers/recommendations.py
-----------------------------------
What: Serves personalized product recommendations for a customer,
      computed live from their category interests (user_interests,
      populated by the Node backend on every product view) and their
      favorited products, ranked against each candidate product's own
      engagement signals (recommendation_score, average_rating,
      favorites_count).
Why:  Powers the mobile app's "Recommended For You" section on Home,
      via the existing Node backend proxy at GET /api/v1/ai/recommendations/
      products (see backend/src/controllers/ai.controller.js
      getProductRecommendations) - clients call the Node backend, which
      calls this service, not the other way around.

REPLACES a previous 501 stub - this router was referenced by main.py but
the real implementation had never been written, so GET /recommendations/
always returned {"status": "not_implemented"}.

Response shape (`recommendations`, `method`) matches exactly what
ai.controller.js already expects to forward on - the query param is
`top_n` for the same reason (that's what the existing Node proxy sends).
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import get_products, get_user_interests, get_user_favorites
from app.services.recommendations_engine import get_recommendations

router = APIRouter()


@router.get("/products")
def recommended_products(
    user_id: Optional[str] = Query(
        None,
        description="Customer's user ID. Omit for anonymous/general recommendations (falls back to top-quality products, not personalized).",
    ),
    top_n: int = Query(10, ge=1, le=50),
):
    """Returns personalized product recommendations for a user."""
    try:
        products = get_products()
        if not products:
            return {"recommendations": [], "method": "general", "based_on_categories": [], "count": 0}

        user_interests = get_user_interests(user_id) if user_id else []
        favorite_ids = get_user_favorites(user_id) if user_id else []

        result = get_recommendations(products, user_interests, favorite_ids, top_n)
        recommendations = result["products"]

        return {
            "recommendations": recommendations,
            "method": "personalized" if result["personalized"] else "general",
            "based_on_categories": result["based_on_categories"],
            "count": len(recommendations),
        }

    except Exception as e:
        print(f"Error generating recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")