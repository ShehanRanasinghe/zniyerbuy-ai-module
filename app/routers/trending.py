from fastapi import APIRouter, HTTPException
import pandas as pd
from app.database import get_products, get_user_interactions
from typing import Optional

router = APIRouter()

@router.get("/products")
def get_trending_products(limit: int = 5, category: Optional[str] = None):
    """
    Get trending products based on views, favorites, and recent activity.
    Trending score = views + (favorites * 2) + (purchases * 3)
    """
    try:
        # Fetch products from Supabase
        products_data = get_products()
        
        if not products_data or len(products_data) == 0:
            raise HTTPException(status_code=503, detail="No products available in database")
        
        # Filter by category if specified
        if category:
            products_data = [
                p for p in products_data 
                if p.get("category", "").lower() == category.lower()
            ]
            
            if not products_data:
                return {
                    "trending_products": [],
                    "method": "engagement_analysis",
                    "total": 0,
                    "note": f"No products found in category: {category}"
                }
        
        # Calculate trending score for each product
        trending_products = []
        for product in products_data:
            views = product.get("views", 0)
            favorites = product.get("favorites_count", 0)
            # Estimate purchases from interaction data or use a default
            purchases = product.get("purchase_count", 0)
            
            trending_score = views + (favorites * 2) + (purchases * 3)
            
            trending_products.append({
                "product_id": product["id"],
                "name": product.get("name", "Unknown"),
                "category": product.get("category", "General"),
                "price": product.get("price", 0),
                "views": views,
                "favorites": favorites,
                "purchases": purchases,
                "trending_score": trending_score,
                "average_rating": product.get("average_rating", 0)
            })
        
        # Sort by trending score
        trending_products.sort(key=lambda x: x["trending_score"], reverse=True)
        
        return {
            "trending_products": trending_products[:limit],
            "method": "engagement_analysis",
            "total": len(trending_products),
            "category_filter": category if category else "all"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching trending products: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending products: {str(e)}")

@router.get("/categories")
def get_trending_categories():
    """
    Get trending categories based on aggregate product engagement.
    """
    try:
        # Fetch products from Supabase
        products_data = get_products()
        
        if not products_data or len(products_data) == 0:
            raise HTTPException(status_code=503, detail="No products available in database")
        
        # Convert to DataFrame for easier aggregation
        df = pd.DataFrame(products_data)
        
        # Ensure required columns exist
        if 'category' not in df.columns:
            return {
                "trending_categories": [],
                "note": "Category information not available"
            }
        
        # Fill missing values
        df['views'] = df.get('views', 0).fillna(0)
        df['favorites_count'] = df.get('favorites_count', 0).fillna(0)
        
        # Group by category and aggregate
        category_stats = df.groupby("category").agg(
            total_views=("views", "sum"),
            total_favorites=("favorites_count", "sum"),
            product_count=("id", "count"),
            avg_price=("price", "mean")
        ).reset_index()
        
        # Calculate trending score
        category_stats["trending_score"] = (
            category_stats["total_views"] + 
            category_stats["total_favorites"] * 2
        )
        
        # Sort by trending score
        category_stats = category_stats.sort_values("trending_score", ascending=False)
        
        # Convert to dict
        trending_categories = category_stats.to_dict(orient="records")
        
        # Format the response
        formatted_categories = []
        for cat in trending_categories:
            formatted_categories.append({
                "category": cat["category"],
                "total_views": int(cat["total_views"]),
                "total_favorites": int(cat["total_favorites"]),
                "product_count": int(cat["product_count"]),
                "avg_price": round(float(cat["avg_price"]), 2),
                "trending_score": int(cat["trending_score"])
            })
        
        return {
            "trending_categories": formatted_categories,
            "method": "category_aggregation",
            "total_categories": len(formatted_categories)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching trending categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending categories: {str(e)}")
