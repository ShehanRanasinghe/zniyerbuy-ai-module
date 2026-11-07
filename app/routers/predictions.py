from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from app.database import get_sales_data, get_products
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

router = APIRouter()

def predict_revenue_for_period(df_shop: pd.DataFrame, days: int = 30) -> Dict[str, Any]:
    """
    Predict next month's revenue and 30-day daily forecast based on shop order history.
    Enforces realistic growth bounds (-15% to +25%) to prevent wild linear extrapolation spikes.
    """
    try:
        if df_shop.empty:
            return {
                "predicted_revenue": None,
                "predicted_revenue_growth_pct": None,
                "daily_revenue_forecast": []
            }
        
        amount_col = 'total_amount' if 'total_amount' in df_shop.columns else 'amount' if 'amount' in df_shop.columns else None
        if not amount_col:
            return {
                "predicted_revenue": None,
                "predicted_revenue_growth_pct": None,
                "daily_revenue_forecast": []
            }
        
        revenues = pd.to_numeric(df_shop[amount_col], errors='coerce').dropna().tolist()
        revenues = [r for r in revenues if r > 0]
        
        if not revenues:
            return {
                "predicted_revenue": None,
                "predicted_revenue_growth_pct": None,
                "daily_revenue_forecast": []
            }
        
        current_total = sum(revenues)
        
        # Determine growth trend from history if multiple orders exist
        if len(revenues) >= 2:
            x = np.array(range(len(revenues))).reshape(-1, 1)
            y = np.array(revenues)
            model = LinearRegression()
            model.fit(x, y)
            slope = model.coef_[0]
            avg_val = np.mean(y)
            raw_growth_pct = (slope / avg_val * 100) if avg_val > 0 else 5.0
            # Clamp growth rate to a realistic, sensible range (-15% to +25%)
            growth_pct = max(-15.0, min(25.0, raw_growth_pct))
        else:
            growth_pct = 10.0  # Realistic default baseline growth for new shops
        
        # Calculate predicted monthly total and daily target
        predicted_total = current_total * (1.0 + (growth_pct / 100.0))
        target_daily_avg = predicted_total / days
        
        # Build 30-day forecast with smooth realistic daily variation
        daily_forecast = []
        base_date = datetime.now()
        
        for i in range(days):
            variation = 1.0 + (0.05 * np.sin(i * 0.5))
            daily_rev = max(0.0, target_daily_avg * variation)
            forecast_date = base_date + timedelta(days=i)
            daily_forecast.append({
                "day": f"Day {i+1}",
                "date": forecast_date.strftime("%Y-%m-%d"),
                "revenue": round(float(daily_rev), 2)
            })
        
        predicted_total = sum(p["revenue"] for p in daily_forecast)
        
        return {
            "predicted_revenue": round(predicted_total, 2),
            "predicted_revenue_growth_pct": round(float(growth_pct), 1),
            "daily_revenue_forecast": daily_forecast
        }
        
    except Exception as e:
        print(f"Error predicting revenue: {e}")
        return {
            "predicted_revenue": None,
            "predicted_revenue_growth_pct": None,
            "daily_revenue_forecast": []
        }

def predict_user_traffic(df_shop: pd.DataFrame, growth_pct: float) -> Dict[str, Any]:
    """
    Estimate expected unique users next month based on active customer history & growth rate.
    """
    try:
        if df_shop.empty:
            return {
                "expected_users": None,
                "expected_users_growth_pct": None
            }
        
        # Count unique customers if customer_id/phone available, else order count
        if 'customer_id' in df_shop.columns and df_shop['customer_id'].dropna().nunique() > 0:
            current_users = df_shop['customer_id'].dropna().nunique()
        elif 'customer_phone' in df_shop.columns and df_shop['customer_phone'].dropna().nunique() > 0:
            current_users = df_shop['customer_phone'].dropna().nunique()
        else:
            current_users = max(1, len(df_shop))
        
        expected_users = max(1, round(current_users * (1.0 + (growth_pct / 100.0))))
        
        return {
            "expected_users": int(expected_users),
            "expected_users_growth_pct": round(float(growth_pct), 1)
        }
        
    except Exception as e:
        print(f"Error predicting users: {e}")
        return {
            "expected_users": None,
            "expected_users_growth_pct": None
        }

def predict_top_category_sales(shop_id: str) -> Dict[str, Any]:
    """
    Predict top selling product category and forecasted sales count.
    """
    try:
        products_data = get_products()
        sales_data = get_sales_data()
        
        df_products = pd.DataFrame(products_data) if products_data else pd.DataFrame()
        if not df_products.empty and 'shop_id' in df_products.columns:
            shop_products = df_products[df_products['shop_id'] == shop_id]
        else:
            shop_products = df_products
            
        categories_in_shop = shop_products['category'].dropna().unique().tolist() if not shop_products.empty and 'category' in shop_products.columns else []
        if not categories_in_shop:
            categories_in_shop = ['Fashion & Clothing']

        df_sales = pd.DataFrame(sales_data) if sales_data else pd.DataFrame()
        if not df_sales.empty and 'shop_id' in df_sales.columns:
            df_sales = df_sales[df_sales['shop_id'] == shop_id]
            
        category_counts = {}
        if not df_sales.empty and 'product_id' in df_sales.columns and not shop_products.empty and 'id' in shop_products.columns:
            df_merged = df_sales.merge(shop_products[['id', 'category']], left_on='product_id', right_on='id', how='left')
            if 'category' in df_merged.columns:
                for cat, group in df_merged.groupby('category'):
                    if pd.notna(cat):
                        category_counts[str(cat)] = len(group)
        
        # Ensure shop categories exist with default counts
        for cat in categories_in_shop:
            if cat not in category_counts:
                category_counts[cat] = 1
                
        top_cat = max(category_counts, key=category_counts.get) if category_counts else categories_in_shop[0]
        top_sales = category_counts.get(top_cat, 1)
        predicted_top_sales = max(1, round(top_sales * 1.15))
        
        category_predictions = []
        for cat, curr_count in category_counts.items():
            category_predictions.append({
                "name": str(cat),
                "current": int(curr_count),
                "predicted": max(1, round(curr_count * 1.15))
            })
            
        return {
            "top_category": str(top_cat),
            "top_category_predicted_sales": int(predicted_top_sales),
            "category_sales_prediction": category_predictions
        }
        
    except Exception as e:
        print(f"Error predicting categories: {e}")
        return {
            "top_category": None,
            "top_category_predicted_sales": None,
            "category_sales_prediction": []
        }

@router.get("/shop/{shop_id}")
def get_shop_predictions(shop_id: str):
    """
    Get comprehensive AI predictions for a shop including:
    - Revenue predictions for next 30 days
    - User traffic predictions
    - Top category sales predictions
    - Category sales breakdown
    """
    try:
        sales_data = get_sales_data()
        
        if not sales_data:
            return {
                "status": "no_data",
                "message": "No sales data available for this shop",
                "predicted_revenue": None,
                "predicted_revenue_growth_pct": None,
                "predicted_daily_revenue": None,
                "expected_users": None,
                "expected_users_growth_pct": None,
                "top_category": None,
                "top_category_predicted_sales": None,
                "daily_revenue_forecast": [],
                "category_sales_prediction": []
            }
        
        df = pd.DataFrame(sales_data)
        
        if 'shop_id' in df.columns:
            df = df[df['shop_id'] == shop_id]
            
        # Exclude cancelled orders
        if not df.empty and 'status' in df.columns:
            df = df[df['status'] != 'cancelled']
            
        if df.empty:
            return {
                "status": "no_data",
                "message": f"No active order history found for shop {shop_id}",
                "predicted_revenue": None,
                "predicted_revenue_growth_pct": None,
                "predicted_daily_revenue": None,
                "expected_users": None,
                "expected_users_growth_pct": None,
                "top_category": None,
                "top_category_predicted_sales": None,
                "daily_revenue_forecast": [],
                "category_sales_prediction": []
            }
        
        revenue_predictions = predict_revenue_for_period(df, days=30)
        growth_pct = revenue_predictions.get("predicted_revenue_growth_pct") or 5.0
        
        user_predictions = predict_user_traffic(df, growth_pct=growth_pct)
        category_predictions = predict_top_category_sales(shop_id)
        
        predicted_daily_revenue = None
        if revenue_predictions["predicted_revenue"]:
            predicted_daily_revenue = round(revenue_predictions["predicted_revenue"] / 30, 2)
            
        return {
            "status": "ok",
            "predicted_revenue": revenue_predictions["predicted_revenue"],
            "predicted_revenue_growth_pct": revenue_predictions["predicted_revenue_growth_pct"],
            "predicted_daily_revenue": predicted_daily_revenue,
            "expected_users": user_predictions["expected_users"],
            "expected_users_growth_pct": user_predictions["expected_users_growth_pct"],
            "top_category": category_predictions["top_category"],
            "top_category_predicted_sales": category_predictions["top_category_predicted_sales"],
            "daily_revenue_forecast": revenue_predictions["daily_revenue_forecast"],
            "category_sales_prediction": category_predictions["category_sales_prediction"]
        }
        
    except Exception as e:
        print(f"Error getting shop predictions: {e}")
        return {
            "status": "error",
            "message": f"Failed to generate predictions: {str(e)}",
            "predicted_revenue": None,
            "predicted_revenue_growth_pct": None,
            "predicted_daily_revenue": None,
            "expected_users": None,
            "expected_users_growth_pct": None,
            "top_category": None,
            "top_category_predicted_sales": None,
            "daily_revenue_forecast": [],
            "category_sales_prediction": []
        }
