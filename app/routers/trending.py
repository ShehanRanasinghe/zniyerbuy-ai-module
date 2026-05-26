from fastapi import APIRouter
import pandas as pd

router = APIRouter()

# Mock product view/purchase frequency data
trending_data = [
    {"product_id": 103, "name": "Green Tomatoes 1kg", "category": "Vegetables", "price": 220, "views": 520, "purchases": 330},
    {"product_id": 108, "name": "Gotukola Bundles", "category": "Vegetables", "price": 60, "views": 480, "purchases": 310},
    {"product_id": 101, "name": "Samba Rice 5kg", "category": "Rice & Grains", "price": 1450, "views": 450, "purchases": 280},
    {"product_id": 107, "name": "Dhal 1kg", "category": "Rice & Grains", "price": 420, "views": 420, "purchases": 260},
    {"product_id": 106, "name": "Coconut Oil 500ml", "category": "Cooking Oils", "price": 760, "views": 390, "purchases": 240},
    {"product_id": 104, "name": "Anchor Milk Powder 400g", "category": "Dairy", "price": 1890, "views": 360, "purchases": 220},
    {"product_id": 105, "name": "Kurakkan Flour 1kg", "category": "Rice & Grains", "price": 560, "views": 340, "purchases": 200},
    {"product_id": 102, "name": "Ceylon Pepper 100g", "category": "Spices", "price": 380, "views": 310, "purchases": 180},
]

@router.get("/products")
def get_trending_products(limit: int = 5, category: str = None):
    try:
        data = trending_data.copy()

        if category:
            data = [p for p in data if p["category"].lower() == category.lower()]

        # Calculate trending score (views + purchases * 2)
        for product in data:
            product["trending_score"] = product["views"] + (product["purchases"] * 2)

        # Sort by trending score
        data.sort(key=lambda x: x["trending_score"], reverse=True)

        return {
            "trending_products": data[:limit],
            "method": "frequency_analysis",
            "total": len(data)
        }

    except Exception as e:
        return {"error": str(e)}

@router.get("/categories")
def get_trending_categories():
    try:
        df = pd.DataFrame(trending_data)
        category_stats = df.groupby("category").agg(
            total_views=("views", "sum"),
            total_purchases=("purchases", "sum"),
            product_count=("product_id", "count")
        ).reset_index()

        category_stats["trending_score"] = (
            category_stats["total_views"] + category_stats["total_purchases"] * 2
        )
        category_stats = category_stats.sort_values("trending_score", ascending=False)

        return {
            "trending_categories": category_stats.to_dict(orient="records")
        }

    except Exception as e:
        return {"error": str(e)}