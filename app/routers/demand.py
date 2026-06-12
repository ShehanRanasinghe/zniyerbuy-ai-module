from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from app.database import get_sales_data, get_products
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter()

def predict_demand(sales_history: list) -> dict:
    """
    Predict future demand using linear regression.
    Returns prediction and trend direction.
    """
    try:
        if not sales_history or len(sales_history) < 2:
            return {
                "prediction": 0,
                "trend": "insufficient_data",
                "confidence": 0
            }
        
        # Prepare data for linear regression
        x = np.array(range(len(sales_history))).reshape(-1, 1)
        y = np.array(sales_history)
        
        # Train model
        model = LinearRegression()
        model.fit(x, y)
        
        # Predict next period
        next_period = np.array([[len(sales_history)]])
        prediction = model.predict(next_period)[0]
        
        # Calculate trend
        current_value = sales_history[-1]
        trend = "increasing" if prediction > current_value else "decreasing"
        
        # Calculate confidence (R² score)
        confidence = model.score(x, y)
        
        return {
            "prediction": round(float(prediction), 2),
            "trend": trend,
            "confidence": round(float(confidence), 2),
            "slope": round(float(model.coef_[0]), 2)
        }
        
    except Exception as e:
        print(f"Error predicting demand: {e}")
        return {
            "prediction": 0,
            "trend": "error",
            "confidence": 0
        }

@router.post("/predict")
def predict_product_demand(product_id: Optional[str] = None, days: int = 7):
    """
    Predict product demand for the next period based on historical sales data.
    If product_id is provided, returns prediction for that product.
    Otherwise, returns predictions for all products.
    """
    try:
        # Fetch sales data from Supabase
        sales_data = get_sales_data()
        products_data = get_products()
        
        if not sales_data or len(sales_data) == 0:
            raise HTTPException(
                status_code=503,
                detail="No sales data available. Please ensure sales records exist in the database."
            )
        
        if not products_data or len(products_data) == 0:
            raise HTTPException(status_code=503, detail="No products available in database")
        
        # Convert to DataFrame
        df = pd.DataFrame(sales_data)
        products_df = pd.DataFrame(products_data)
        
        # Ensure required columns exist
        required_columns = ['product_id', 'quantity', 'sale_date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=500,
                detail=f"Sales data missing required columns: {missing_columns}"
            )
        
        # Convert sale_date to datetime
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        
        # Filter by product_id if specified
        if product_id:
            df = df[df['product_id'] == product_id]
            if df.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No sales data found for product_id: {product_id}"
                )
        
        # Group by product and date, sum quantities
        daily_sales = df.groupby(['product_id', pd.Grouper(key='sale_date', freq='D')])['quantity'].sum().reset_index()
        
        # Generate predictions for each product
        predictions = []
        
        for pid in daily_sales['product_id'].unique():
            product_sales = daily_sales[daily_sales['product_id'] == pid]
            
            # Get product details
            product_info = products_df[products_df['id'] == pid]
            if product_info.empty:
                continue
            
            product_name = product_info.iloc[0].get('name', 'Unknown')
            
            # Get sales history (last 30 days or available data)
            sales_history = product_sales.sort_values('sale_date')['quantity'].tolist()
            
            if len(sales_history) < 2:
                continue
            
            # Predict demand
            demand_prediction = predict_demand(sales_history)
            
            predictions.append({
                "product_id": pid,
                "product_name": product_name,
                "current_sales": sales_history[-1] if sales_history else 0,
                "predicted_demand": demand_prediction["prediction"],
                "trend": demand_prediction["trend"],
                "confidence": demand_prediction["confidence"],
                "historical_data_points": len(sales_history),
                "prediction_period_days": days
            })
        
        if not predictions:
            return {
                "predictions": [],
                "model": "linear_regression",
                "note": "Insufficient sales data for demand prediction"
            }
        
        # Sort by predicted demand
        predictions.sort(key=lambda x: x["predicted_demand"], reverse=True)
        
        # If specific product requested, return only that
        if product_id:
            return {
                "product_id": product_id,
                "prediction": predictions[0] if predictions else None,
                "model": "linear_regression",
                "prediction_period_days": days
            }
        
        return {
            "predictions": predictions,
            "model": "linear_regression",
            "total_products": len(predictions),
            "prediction_period_days": days
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error predicting demand: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to predict demand: {str(e)}")

@router.get("/predict")
def get_demand_prediction(product_id: Optional[str] = None, days: int = 7):
    """
    GET endpoint for demand prediction (calls POST endpoint internally).
    """
    return predict_product_demand(product_id, days)
