"""
app/services/trending_engine.py
-----------------------------------
What: Computes trending products and trending categories from recent
      user_interactions activity (view, save, click_deal, search,
      purchase), weighted by action type and how recent each interaction
      is. Falls back to all-time engagement metrics (recommendation_score,
      favorites_count, views) when there isn't enough recent interaction
      data yet - e.g. a freshly-seeded database, or a quiet week.
Why:  "Trending" should mean "hot right now", not just "historically
      popular" - that's what products.recommendation_score / views already
      cover elsewhere (see products.service.js getTrendingProducts on the
      Node backend). This module is what makes /trending/products and
      /trending/categories genuinely reflect *recent* customer behavior.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict
from collections import defaultdict

# Recent user actions are the trending signal; not all actions carry the
# same intent strength, so purchases and saves count for more than a
# passive view.
ACTION_WEIGHTS = {
    "purchase": 5,
    "save": 3,
    "click_deal": 2,
    "view": 1,
    "search": 0.5,
}

# Below this many distinct trending products, recent interaction data is
# too thin to be a meaningful signal (e.g. a new deployment with barely
# any activity yet) - fall back to all-time engagement instead.
MIN_TRENDING_PRODUCTS = 5


def _parse_dt(value):
    if not value:
        return None
    try:
        s = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _score_interactions(interactions: List[Dict], days: int) -> Dict[str, float]:
    """Returns {product_id: weighted_score} for interactions within the last `days`."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    scores: Dict[str, float] = defaultdict(float)
    for it in interactions:
        product_id = it.get("product_id")
        if not product_id:
            continue
        dt = _parse_dt(it.get("created_at"))
        if dt and dt < cutoff:
            continue
        weight = ACTION_WEIGHTS.get(it.get("action_type"), 1)
        scores[product_id] += weight
    return scores


def get_trending_products(
    products: List[Dict],
    interactions: List[Dict],
    limit: int = 10,
    days: int = 7,
) -> List[Dict]:
    """Returns products ranked by recent interaction activity, most-trending-first."""
    scores = _score_interactions(interactions, days)

    if len(scores) >= MIN_TRENDING_PRODUCTS:
        by_id = {p["id"]: p for p in products}
        ranked_ids = sorted(scores, key=scores.get, reverse=True)
        result = []
        for pid in ranked_ids:
            p = by_id.get(pid)
            if not p:
                continue
            result.append({**p, "trending_score": round(scores[pid], 2)})
            if len(result) >= limit:
                break
        if result:
            return result

    # Fallback: not enough recent interaction data yet - use all-time
    # engagement so the section still shows something reasonable.
    fallback = sorted(
        products,
        key=lambda p: (
            p.get("recommendation_score") or 0,
            p.get("favorites_count") or 0,
            p.get("views") or 0,
        ),
        reverse=True,
    )
    return [{**p, "trending_score": None} for p in fallback[:limit]]


def get_trending_categories(
    products: List[Dict],
    interactions: List[Dict],
    limit: int = 10,
    days: int = 7,
) -> List[Dict]:
    """Returns categories ranked by recent interaction activity, most-trending-first."""
    scores = _score_interactions(interactions, days)
    by_id = {p["id"]: p for p in products}

    category_scores: Dict[str, float] = defaultdict(float)
    category_counts: Dict[str, int] = defaultdict(int)

    for pid, score in scores.items():
        p = by_id.get(pid)
        if not p or not p.get("category"):
            continue
        category_scores[p["category"]] += score
        category_counts[p["category"]] += 1

    if category_scores:
        ranked = sorted(category_scores, key=category_scores.get, reverse=True)
        return [
            {
                "category": cat,
                "trending_score": round(category_scores[cat], 2),
                "product_count": category_counts[cat],
            }
            for cat in ranked[:limit]
        ]

    # Fallback: aggregate all-time product engagement by category.
    fallback_scores: Dict[str, float] = defaultdict(float)
    fallback_counts: Dict[str, int] = defaultdict(int)
    for p in products:
        cat = p.get("category")
        if not cat:
            continue
        fallback_scores[cat] += (p.get("recommendation_score") or 0) + (p.get("favorites_count") or 0) * 0.5
        fallback_counts[cat] += 1

    ranked = sorted(fallback_scores, key=fallback_scores.get, reverse=True)
    return [
        {
            "category": cat,
            "trending_score": None,
            "product_count": fallback_counts[cat],
        }
        for cat in ranked[:limit]
    ]