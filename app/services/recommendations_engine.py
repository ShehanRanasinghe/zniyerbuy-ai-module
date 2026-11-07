"""
app/services/recommendations_engine.py
-----------------------------------
What: Builds personalized product recommendations for a single user,
      combining:
        - user_interests category scores (explicit signal: which
          categories this user views often - populated by the Node
          backend's update_user_interest RPC on every product view, see
          recommendation.service.js trackProductView)
        - the user's favorited products' categories (a secondary implicit
          signal, useful before user_interests has accumulated much)
        - each candidate product's own quality signals
          (recommendation_score, average_rating, favorites_count), used
          both as a tiebreaker and as the entire ranking for a cold-start
          user with no history yet
Why:  Powers the mobile app's "Recommended For You" section. A user with
      no interaction history at all still gets a sensible, non-empty
      response (general top-quality products) rather than an empty list.
"""

from typing import List, Dict
from collections import defaultdict


def _category_weights(user_interests: List[Dict], favorited_products: List[Dict]) -> Dict[str, float]:
    weights: Dict[str, float] = defaultdict(float)
    for interest in user_interests:
        cat = interest.get("category")
        if cat:
            weights[cat] += interest.get("score") or 1
    for p in favorited_products:
        cat = p.get("category")
        if cat:
            weights[cat] += 1  # smaller implicit boost than an explicit view-driven interest score
    return weights


def _quality_score(p: Dict) -> float:
    return (
        (p.get("recommendation_score") or 0) * 1.0
        + (p.get("average_rating") or 0) * 2.0
        + (p.get("favorites_count") or 0) * 0.3
    )


def get_recommendations(
    products: List[Dict],
    user_interests: List[Dict],
    favorite_product_ids: List[str],
    limit: int = 10,
) -> Dict:
    """
    Returns {personalized, based_on_categories, products}.
    `personalized` is False when the user has no category signal yet (new
    user / anonymous request), in which case `products` is simply ranked
    by general quality — still useful, just not tailored to them.
    """
    favorited_set = set(favorite_product_ids)
    favorited_products = [p for p in products if p.get("id") in favorited_set]
    category_weights = _category_weights(user_interests, favorited_products)

    # Don't recommend products the user has already favorited/saved.
    candidates = [
        p for p in products
        if p.get("id") not in favorited_set and p.get("is_available", True)
    ]

    is_personalized = bool(category_weights)

    def score(p: Dict) -> float:
        cat_boost = category_weights.get(p.get("category"), 0) * 5.0
        return cat_boost + _quality_score(p)

    ranked = sorted(candidates, key=score, reverse=True)
    top_categories = sorted(category_weights, key=category_weights.get, reverse=True)[:3]

    return {
        "personalized": is_personalized,
        "based_on_categories": top_categories,
        "products": ranked[:limit],
    }