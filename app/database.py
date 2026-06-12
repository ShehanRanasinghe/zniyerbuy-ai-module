import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

# Create Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Failed to create Supabase client: {e}")
    raise

def get_user_interactions() -> List[Dict]:
    """
    Fetch user interaction data from Supabase.
    Returns list of interaction records with user_id, product_id, and rating/interaction_type.
    """
    try:
        # Try to fetch from user_interactions table
        response = supabase.table("user_interactions").select("*").execute()
        
        if response.data and len(response.data) > 0:
            return response.data
        
        # Fallback: try to fetch from favorites table as interactions
        favorites_response = supabase.table("favorites").select("user_id, product_id").execute()
        
        if favorites_response.data and len(favorites_response.data) > 0:
            # Convert favorites to interaction format (rating = 5 for favorites)
            interactions = []
            for fav in favorites_response.data:
                interactions.append({
                    "user_id": fav["user_id"],
                    "product_id": fav["product_id"],
                    "rating": 5,  # Favorites are considered high-value interactions
                    "interaction_type": "favorite"
                })
            return interactions
        
        print("No user interaction data found in database")
        return []
        
    except Exception as e:
        print(f"Error fetching user interactions: {e}")
        return []

def get_products() -> List[Dict]:
    """
    Fetch all products from Supabase.
    Returns list of product records with id, name, category, price, views, favorites_count, etc.
    """
    try:
        response = supabase.table("products").select("*").execute()
        
        if response.data and len(response.data) > 0:
            return response.data
        
        print("No products found in database")
        return []
        
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

def get_sales_data() -> List[Dict]:
    """
    Fetch sales data from Supabase.
    Returns list of sales records with product_id, quantity, sale_date, etc.
    """
    try:
        # Try to fetch from sales or orders table
        response = supabase.table("sales").select("*").execute()
        
        if response.data and len(response.data) > 0:
            return response.data
        
        # Fallback: try orders table
        orders_response = supabase.table("orders").select("*").execute()
        
        if orders_response.data and len(orders_response.data) > 0:
            return orders_response.data
        
        print("No sales data found in database")
        return []
        
    except Exception as e:
        print(f"Error fetching sales data: {e}")
        return []

def get_product_by_id(product_id: str) -> Optional[Dict]:
    """
    Fetch a single product by ID from Supabase.
    Returns product record or None if not found.
    """
    try:
        response = supabase.table("products").select("*").eq("id", product_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        print(f"Product not found: {product_id}")
        return None
        
    except Exception as e:
        print(f"Error fetching product {product_id}: {e}")
        return None

def get_trending_products(limit: int = 10) -> List[Dict]:
    """
    Fetch trending products from Supabase based on views and favorites.
    Returns list of products sorted by engagement.
    """
    try:
        response = supabase.table("products") \
            .select("*") \
            .order("views", desc=True) \
            .limit(limit) \
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data
        
        print("No trending products found")
        return []
        
    except Exception as e:
        print(f"Error fetching trending products: {e}")
        return []

def get_user_favorites(user_id: str) -> List[Dict]:
    """
    Fetch user's favorite products from Supabase.
    Returns list of product IDs favorited by the user.
    """
    try:
        response = supabase.table("favorites") \
            .select("product_id") \
            .eq("user_id", user_id) \
            .execute()
        
        if response.data and len(response.data) > 0:
            return [fav["product_id"] for fav in response.data]
        
        return []
        
    except Exception as e:
        print(f"Error fetching user favorites: {e}")
        return []

def health_check() -> Dict:
    """
    Check database connection health.
    Returns status and connection info.
    """
    try:
        # Try a simple query to test connection
        response = supabase.table("products").select("id").limit(1).execute()
        
        return {
            "status": "connected",
            "database": "supabase",
            "url": SUPABASE_URL,
            "tables_accessible": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "database": "supabase",
            "url": SUPABASE_URL,
            "error": str(e),
            "tables_accessible": False
        }
