import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_interactions():
    try:
        response = supabase.table("user_interactions").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching user interactions: {e}")
        return []

def get_products():
    try:
        response = supabase.table("products").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

def get_sales_data():
    try:
        response = supabase.table("sales").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching sales data: {e}")
        return []