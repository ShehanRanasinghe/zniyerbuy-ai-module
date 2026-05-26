from fastapi import APIRouter
from pydantic import BaseModel
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

router = APIRouter()

# Mock user-product interaction data (will be replaced with Supabase data in task 7.2)
interaction_data = {
    "user_id": [1, 1, 1, 2, 2, 3, 3, 3, 4, 4, 5, 5],
    "product_id": [101, 102, 103, 101, 104, 102, 103, 105, 101, 105, 103, 104],
    "rating": [5, 4, 3, 4, 5, 3, 4, 5, 2, 4, 5, 3],
}

products = {
    101: {"name": "Samba Rice 5kg", "category": "Rice & Grains", "price": 1450},
    102: {"name": "Ceylon Pepper 100g", "category": "Spices", "price": 380},
    103: {"name": "Green Tomatoes 1kg", "category": "Vegetables", "price": 220},
    104: {"name": "Anchor Milk Powder 400g", "category": "Dairy", "price": 1890},
    105: {"name": "Kurakkan Flour 1kg", "category": "Rice & Grains", "price": 560},
    106: {"name": "Coconut Oil 500ml", "category": "Cooking Oils", "price": 760},
    107: {"name": "Dhal 1kg", "category": "Rice & Grains", "price": 420},
    108: {"name": "Gotukola Bundles", "category": "Vegetables", "price": 60},
}

def build_model():
    df = pd.DataFrame(interaction_data)
    user_product_matrix = df.pivot_table(
        index="user_id", columns="product_id", values="rating", fill_value=0
    )
    model = NearestNeighbors(metric="cosine", algorithm="brute", n_neighbors=3)
    model.fit(user_product_matrix.values)
    return model, user_product_matrix

model, user_product_matrix = build_model()

class RecommendationRequest(BaseModel):
    user_id: int
    top_n: int = 5

@router.get("/products")
def get_recommendations(user_id: int = 1, top_n: int = 5):
    try:
        if user_id not in user_product_matrix.index:
            # New user — return top rated products
            return {
                "user_id": user_id,
                "recommendations": [
                    {"product_id": pid, **info}
                    for pid, info in list(products.items())[:top_n]
                ],
                "method": "popular"
            }

        user_idx = user_product_matrix.index.get_loc(user_id)
        user_vector = user_product_matrix.iloc[user_idx].values.reshape(1, -1)
        distances, indices = model.kneighbors(user_vector)

        similar_users = [
            user_product_matrix.index[i]
            for i in indices.flatten()
            if user_product_matrix.index[i] != user_id
        ]

        already_rated = set(
            user_product_matrix.columns[user_product_matrix.loc[user_id] > 0]
        )

        recommended = []
        for similar_user in similar_users:
            rated_by_similar = set(
                user_product_matrix.columns[user_product_matrix.loc[similar_user] > 0]
            )
            new_products = rated_by_similar - already_rated
            for pid in new_products:
                if pid in products and len(recommended) < top_n:
                    recommended.append({"product_id": int(pid), **products[pid]})

        if not recommended:
            recommended = [
                {"product_id": pid, **info}
                for pid, info in list(products.items())[:top_n]
            ]

        return {
            "user_id": user_id,
            "recommendations": recommended,
            "method": "collaborative_filtering"
        }

    except Exception as e:
        return {"error": str(e)}