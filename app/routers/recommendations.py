from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from app.database import get_user_interactions, get_products
from sklearn.neighbors import NearestNeighbors
from typing import Optional

router = APIRouter()

class RecommendationRequest(BaseModel):
    user_id: int
    top_n: int = 5

def build_recommendation_model(interactions_data, products_data):
    """
    Build collaborative filtering model from user interaction data.
    Returns model and user-product matrix.
    """
    try:
        if not interactions_data or len(interactions_data) == 0:
            return None, None
        
        # Convert to DataFrame
        df = pd.DataFrame(interactions_data)
        
        # Create user-product matrix
        user_product_matrix = df.pivot_table(
            index='user_id',
            columns='product_id',
            values='rating',
            fill_value=0
        )
        
        # Build KNN model
        model = NearestNeighbors(metric='cosine', algorithm='brute')
        model.fit(user_product_matrix.values)
        
        return model, user_product_matrix
    except Exception as e:
        print(f"Error building recommendation model: {e}")
        return None, None

@router.get("/products")
def get_recommendations(user_id: int = 1, top_n: int = 5):
    """
    Get personalized product recommendations for a user.
    Uses collaborative filtering based on user interactions.
    Falls back to popular products if no interaction data exists.
    """
    try:
        # Fetch data from Supabase
        interactions_data = get_user_interactions()
        products_data = get_products()
        
        if not products_data or len(products_data) == 0:
            raise HTTPException(status_code=503, detail="No products available in database")
        
        # Convert products to dict for easy lookup
        products_dict = {p["id"]: p for p in products_data}
        
        # If no interaction data, return popular products
        if not interactions_data or len(interactions_data) == 0:
            # Sort by views or favorites_count if available
            sorted_products = sorted(
                products_data,
                key=lambda x: x.get('views', 0) + x.get('favorites_count', 0) * 2,
                reverse=True
            )[:top_n]
            
            return {
                "user_id": user_id,
                "recommendations": [
                    {
                        "product_id": p["id"],
                        "name": p.get("name", "Unknown"),
                        "category": p.get("category", "General"),
                        "price": p.get("price", 0),
                        "views": p.get("views", 0),
                        "favorites_count": p.get("favorites_count", 0)
                    }
                    for p in sorted_products
                ],
                "method": "popular_products",
                "note": "No interaction data available, showing popular products"
            }
        
        # Build recommendation model
        model, user_product_matrix = build_recommendation_model(interactions_data, products_data)
        
        if model is None or user_product_matrix is None:
            raise HTTPException(status_code=500, detail="Failed to build recommendation model")
        
        # Check if user exists in interaction data
        if user_id not in user_product_matrix.index:
            # New user - return popular products
            sorted_products = sorted(
                products_data,
                key=lambda x: x.get('views', 0) + x.get('favorites_count', 0) * 2,
                reverse=True
            )[:top_n]
            
            return {
                "user_id": user_id,
                "recommendations": [
                    {
                        "product_id": p["id"],
                        "name": p.get("name", "Unknown"),
                        "category": p.get("category", "General"),
                        "price": p.get("price", 0)
                    }
                    for p in sorted_products
                ],
                "method": "popular_products",
                "note": "New user, showing popular products"
            }
        
        # Get user's vector and find similar users
        user_idx = user_product_matrix.index.get_loc(user_id)
        user_vector = user_product_matrix.iloc[user_idx].values.reshape(1, -1)
        distances, indices = model.kneighbors(user_vector, n_neighbors=min(6, len(user_product_matrix)))
        
        # Get similar users (excluding the user themselves)
        similar_users = [
            user_product_matrix.index[i]
            for i in indices.flatten()
            if user_product_matrix.index[i] != user_id
        ]
        
        # Get products already rated by the user
        already_rated = set(
            user_product_matrix.columns[user_product_matrix.loc[user_id] > 0]
        )
        
        # Find products rated by similar users but not by current user
        recommended = []
        for similar_user in similar_users:
            rated_by_similar = set(
                user_product_matrix.columns[user_product_matrix.loc[similar_user] > 0]
            )
            new_products = rated_by_similar - already_rated
            
            for pid in new_products:
                if pid in products_dict and len(recommended) < top_n:
                    product = products_dict[pid]
                    recommended.append({
                        "product_id": pid,
                        "name": product.get("name", "Unknown"),
                        "category": product.get("category", "General"),
                        "price": product.get("price", 0)
                    })
        
        # If not enough recommendations, fill with popular products
        if len(recommended) < top_n:
            remaining = top_n - len(recommended)
            recommended_ids = {r["product_id"] for r in recommended}
            
            sorted_products = sorted(
                [p for p in products_data if p["id"] not in recommended_ids and p["id"] not in already_rated],
                key=lambda x: x.get('views', 0) + x.get('favorites_count', 0) * 2,
                reverse=True
            )[:remaining]
            
            for p in sorted_products:
                recommended.append({
                    "product_id": p["id"],
                    "name": p.get("name", "Unknown"),
                    "category": p.get("category", "General"),
                    "price": p.get("price", 0)
                })
        
        return {
            "user_id": user_id,
            "recommendations": recommended[:top_n],
            "method": "collaborative_filtering",
            "similar_users_count": len(similar_users)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")
