# ZniyerBuy AI Module

An intelligent recommendation and analytics service powered by machine learning algorithms, providing personalized product recommendations, demand prediction, trending analysis, and actionable admin insights for the ZniyerBuy marketplace platform.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Core Features](#core-features)
- [Machine Learning Algorithms](#machine-learning-algorithms)
- [API Endpoints](#api-endpoints)
- [Recommendation Engine](#recommendation-engine)
- [Demand Prediction System](#demand-prediction-system)
- [Trending Analysis](#trending-analysis)
- [Admin Insights Generator](#admin-insights-generator)
- [Database Integration](#database-integration)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Performance Optimization](#performance-optimization)

## Overview

The ZniyerBuy AI Module is a FastAPI-based microservice that provides intelligent features for the marketplace platform. It analyzes user behavior, product performance, and platform metrics to deliver personalized experiences and data-driven insights.

**Key Capabilities:**
- **Collaborative Filtering** - Personalized product recommendations based on user similarity
- **Demand Prediction** - Linear regression-based sales forecasting
- **Trending Analysis** - Multi-factor engagement scoring for products and categories
- **Admin Insights** - Rule-based analytics for platform optimization
- **Real-time Processing** - Fast API responses with efficient data processing
- **Scalable Architecture** - Stateless design for horizontal scaling

# ZniyerBuy AI — Prediction Models Documentation

## Overview

This module contains **6 machine learning models** that power the *"Predictions for Next Month"* dashboard panel. Each model is trained on the Instacart-style grocery order dataset located in `/data` and saved as an independent `.pkl` file for clean API integration.

---

## Model Inventory

| # | Model File | Notebook | Algorithm | Target |
|---|---|---|---|---|
| 1 | `revenue_predictor.pkl` | `01_revenue_prediction.ipynb` | Random Forest Regressor | Next month total revenue (Rs.) |
| 2 | `daily_revenue_predictor.pkl` | `02_daily_revenue_avg.ipynb` | Gradient Boosting Regressor | Average daily revenue (Rs.) |
| 3 | `user_traffic_predictor.pkl` | `03_user_traffic_prediction.ipynb` | Ridge Regression + Poly Features | Expected unique users next month |
| 4 | `top_category_classifier.pkl` | `04_top_category_classifier.ipynb` | Random Forest Classifier | Top-revenue department next month |
| 5 | `daily_revenue_forecast.pkl` | `05_daily_revenue_forecast.ipynb` | ARIMA(5,1,2) | 30-day daily revenue series (Rs.) |
| 6 | `category_sales_predictor.pkl` | `06_category_sales_prediction.ipynb` | Multi-Output Random Forest | Unit sales per department next month |

---

## Dataset

| File | Rows | Description |
|---|---|---|
| `orders.csv` | 3.4M | Order history: user_id, order_number, day/hour, days_since_prior |
| `order_products__train.csv` | 1.4M | Products per order + reorder flag |
| `order_products__prior.csv` | 32.4M | Full prior order-product history |
| `products.csv` | 49,688 | Product catalog with aisle + department |
| `departments.csv` | 21 | Department list |
| `aisles.csv` | 134 | Aisle list |

> **Revenue Engineering**: No price column exists in the dataset. Revenue is engineered using a per-department average price proxy (Rs.) assigned based on category (e.g., Produce ≈ Rs. 150, Alcohol ≈ Rs. 800).

---

## File Structure

```
zniyerbuy-ai-module/
├── data/                               # Raw CSV datasets (read-only)
├── models/                             # Trained .pkl model files (output)
│   ├── revenue_predictor.pkl
│   ├── daily_revenue_predictor.pkl
│   ├── user_traffic_predictor.pkl
│   ├── top_category_classifier.pkl
│   ├── daily_revenue_forecast.pkl
│   └── category_sales_predictor.pkl
├── notebooks/                          # Jupyter training notebooks
│   ├── 00_data_exploration.ipynb       # EDA & shared reference
│   ├── 01_revenue_prediction.ipynb
│   ├── 02_daily_revenue_avg.ipynb
│   ├── 03_user_traffic_prediction.ipynb
│   ├── 04_top_category_classifier.ipynb
│   ├── 05_daily_revenue_forecast.ipynb
│   └── 06_category_sales_prediction.ipynb
├── verify_models.py                    # Script to validate all saved models
└── README_MODELS.md                    # This file
```

---

## How to Train Models

### 1. Activate the virtual environment

```bash
# Windows
.\venv\Scripts\activate
```

### 2. Install required libraries

```bash
pip install -r requirements.txt
```

### 3. Run notebooks in order

Open each notebook in Jupyter and run all cells top-to-bottom:

```bash
jupyter notebook notebooks/
```

Run in order: `00` → `01` → `02` → `03` → `04` → `05` → `06`

### 4. Verify all models saved correctly

```bash
python verify_models.py
```

---

## Model Details

### 1. Revenue Predictor (`revenue_predictor.pkl`)

- **Algorithm**: `RandomForestRegressor(n_estimators=300, min_samples_leaf=2)`
- **Features**: Monthly total orders, items, unique users, avg reorder rate, items/order, lag revenue, lag orders, lag users, revenue growth rate
- **Target**: Next month's total revenue (Rs.)
- **Evaluation**: RMSE (Rs.), MAE (Rs.), R², 5-fold CV R²

**API Usage:**
```python
import joblib, numpy as np
model = joblib.load('models/revenue_predictor.pkl')
features = [[total_orders, total_items, unique_users, avg_reorder,
             items_per_order, prev_revenue, prev_orders, prev_users, growth_rate]]
predicted_revenue = model.predict(features)[0]
```

---

### 2. Daily Revenue Predictor (`daily_revenue_predictor.pkl`)

- **Algorithm**: `GradientBoostingRegressor(n_estimators=300, learning_rate=0.05, max_depth=4)`
- **Features**: Day of week, order count, item count, reorder rate, avg hour, items/order, prev same-DOW revenue, DOW growth rate
- **Target**: Average daily revenue for next month (Rs.)

**API Usage:**
```python
model = joblib.load('models/daily_revenue_predictor.pkl')
avg_daily = model.predict([[dow, orders, items, reorder, hour, ipo, prev_rev, growth]])[0]
```

---

### 3. User Traffic Predictor (`user_traffic_predictor.pkl`)

- **Algorithm**: `Pipeline(StandardScaler → PolynomialFeatures(2) → Ridge)` with GridSearchCV alpha tuning
- **Features**: Previous month users, 2-month lag users, user growth rate, 3-month rolling avg, prev orders, avg days between orders, orders per user
- **Target**: Number of unique active users next month

**API Usage:**
```python
model = joblib.load('models/user_traffic_predictor.pkl')
users = int(model.predict([[prev_users, prev2_users, growth, rolling, prev_orders, days_between, freq]])[0])
```

---

### 4. Top Category Classifier (`top_category_classifier.pkl`)

- **Algorithm**: `RandomForestClassifier(n_estimators=500, class_weight='balanced')` + `LabelEncoder`
- **Saved as**: Dict bundle `{model, label_encoder, feature_cols, dept_map}`
- **Features**: Monthly revenue per dept + previous month revenue per dept + growth per dept
- **Target**: Department ID of highest-revenue category next month

**API Usage:**
```python
bundle = joblib.load('models/top_category_classifier.pkl')
pred_label = bundle['model'].predict([features])[0]
dept_id = int(bundle['label_encoder'].inverse_transform([pred_label])[0])
dept_name = bundle['dept_map'][dept_id]
```

---

### 5. Daily Revenue Forecast (`daily_revenue_forecast.pkl`)

- **Algorithm**: `ARIMA(5, 1, 2)` from `statsmodels`
- **Saved as**: Dict bundle `{model_result, forecast_30_days, avg_daily, total_forecast, ...}`
- **Target**: List of 30 daily revenue values for the next month (Rs.)

**API Usage:**
```python
bundle = joblib.load('models/daily_revenue_forecast.pkl')
forecast_30 = bundle['forecast_30_days']   # list of 30 float values
avg_daily   = bundle['avg_daily']
total       = bundle['total_forecast']
```

---

### 6. Category Sales Predictor (`category_sales_predictor.pkl`)

- **Algorithm**: `MultiOutputRegressor(RandomForestRegressor(n_estimators=200))` — one RF per department
- **Saved as**: Dict bundle `{model, feature_cols, unit_cols, departments, last_month_units, next_month_pred}`
- **Target**: Unit sales for all 21 departments next month (vector output)

**API Usage:**
```python
bundle = joblib.load('models/category_sales_predictor.pkl')
# Pre-computed prediction already in bundle:
next_preds = bundle['next_month_pred']  # dict: dept_N_units -> predicted_units
# OR real-time predict:
preds = bundle['model'].predict([features])[0]
```

---

## Revenue Proxy Price Table

| Department | Avg Price (Rs.) |
|---|---|
| Produce | 150 |
| Beverages | 180 |
| Bakery | 250 |
| Dry Goods/Pasta | 300 |
| Dairy Eggs | 300 |
| Frozen | 350 |
| Pantry | 350 |
| International | 400 |
| Deli | 400 |
| Household | 450 |
| Personal Care | 500 |
| Babies | 500 |
| Pets | 600 |
| Meat/Seafood | 700 |
| Alcohol | 800 |


## Architecture

### System Design

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌───────────────────────────────────┐  │
│  │   CORS Middleware                 │  │
│  │   - Allow configured origins      │  │
│  │   - Credentials support           │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Request Logging Middleware      │  │
│  │   - Timestamp tracking            │  │
│  │   - Performance monitoring        │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Error Handling Middleware       │  │
│  │   - Global exception catching     │  │
│  │   - Structured error responses    │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   API Routers                     │  │
│  │   - /recommendations              │  │
│  │   - /demand                       │  │
│  │   - /trending                     │  │
│  │   - /insights                     │  │
│  └───────────────────────────────────┘  │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│      Machine Learning Pipeline          │
│  ┌───────────────────────────────────┐  │
│  │   Data Preprocessing              │  │
│  │   - Pandas DataFrames             │  │
│  │   - Missing value handling        │  │
│  │   - Feature engineering           │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Model Training & Inference      │  │
│  │   - KNN (Collaborative Filtering) │  │
│  │   - Linear Regression (Demand)    │  │
│  │   - Engagement Scoring (Trending) │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Result Ranking & Filtering      │  │
│  │   - Score-based sorting           │  │
│  │   - Deduplication                 │  │
│  │   - Top-N selection               │  │
│  └───────────────────────────────────┘  │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│         Supabase Database               │
│  - User interactions (views, favorites) │
│  - Product catalog with metadata        │
│  - Sales history for forecasting        │
│  - Platform statistics                  │
└─────────────────────────────────────────┘
```

### Request Flow

1. **Client Request** → FastAPI endpoint (GET/POST)
2. **CORS Validation** → Check origin and headers
3. **Request Logging** → Log method, path, timestamp
4. **Route Handler** → Map to appropriate router function
5. **Data Fetching** → Query Supabase for required data
6. **Data Preprocessing** → Convert to Pandas DataFrame, handle missing values
7. **ML Processing** → Apply algorithm (KNN, Linear Regression, etc.)
8. **Result Formatting** → Structure response with metadata
9. **Response** → Return JSON with predictions/recommendations
10. **Performance Logging** → Log processing time in headers

## Technology Stack

### Core Technologies

- **Runtime:** Python 3.8+
- **Framework:** FastAPI (async web framework)
- **Server:** Uvicorn (ASGI server)
- **Database Client:** Supabase Python SDK
- **Data Processing:** Pandas, NumPy
- **Machine Learning:** scikit-learn, statsmodels

### Key Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework with automatic API documentation |
| `uvicorn` | ASGI server for production deployment |
| `scikit-learn` | Machine learning algorithms (KNN, Linear Regression) |
| `pandas` | Data manipulation and analysis |
| `numpy` | Numerical computing and array operations |
| `supabase` | Database client for PostgreSQL |
| `python-dotenv` | Environment variable management |
| `statsmodels` | Statistical modeling and time series analysis |
| `httpx` | Async HTTP client for external API calls |
| `websockets` | WebSocket support for real-time features |
| `pyjwt` | JWT token handling for authentication |

## Core Features

### 1. Personalized Recommendations

**Algorithm:** K-Nearest Neighbors (KNN) Collaborative Filtering

**Input:**
- User ID
- Number of recommendations (default: 5)

**Output:**
- List of recommended products with metadata
- Recommendation method used
- Confidence metrics

**Fallback Strategy:**
- If no interaction data → Popular products (by views + favorites)
- If new user → Popular products
- If insufficient similar users → Fill with popular products

### 2. Demand Prediction

**Algorithm:** Linear Regression on Historical Sales

**Input:**
- Product ID (optional - if omitted, predicts for all products)
- Prediction period in days (default: 7)

**Output:**
- Predicted demand quantity
- Trend direction (increasing/decreasing)
- Confidence score (R² value)
- Historical data points used

**Use Cases:**
- Inventory planning
- Restocking alerts
- Seasonal trend identification

### 3. Trending Products

**Algorithm:** Multi-Factor Engagement Scoring

**Input:**
- Limit (number of products to return)
- Category filter (optional)

**Output:**
- Ranked list of trending products
- Engagement metrics (views, favorites, purchases)
- Trending score breakdown

**Scoring Formula:**
```
trending_score = views + (favorites × 2) + (purchases × 3)
```

### 4. Trending Categories

**Algorithm:** Category-Level Aggregation

**Input:** None

**Output:**
- Ranked list of categories
- Aggregate metrics per category
- Product count per category

**Metrics:**
- Total views
- Total favorites
- Product count
- Average price

### 5. Admin Insights

**Algorithm:** Rule-Based Analytics

**Input:**
- Platform statistics (users, shops, products, deals)

**Output:**
- 5 actionable insights
- Data-driven recommendations
- Performance indicators

**Insight Categories:**
- User growth analysis
- Shop verification bottlenecks
- Product quality monitoring
- Deal activity optimization
- Engagement improvement suggestions

## Machine Learning Algorithms

### 1. Collaborative Filtering (K-Nearest Neighbors)

**Purpose:** Find similar users and recommend products they liked

**Algorithm Details:**

```python
from sklearn.neighbors import NearestNeighbors

# Step 1: Create user-product interaction matrix
user_product_matrix = interactions_df.pivot_table(
    index='user_id',
    columns='product_id',
    values='rating',
    fill_value=0
)

# Step 2: Train KNN model
model = NearestNeighbors(
    metric='cosine',      # Cosine similarity for sparse data
    algorithm='brute',    # Exhaustive search for accuracy
    n_neighbors=6         # Find 6 nearest neighbors
)
model.fit(user_product_matrix.values)

# Step 3: Find similar users
user_vector = user_product_matrix.loc[user_id].values.reshape(1, -1)
distances, indices = model.kneighbors(user_vector, n_neighbors=6)

# Step 4: Get products rated by similar users
similar_users = [user_product_matrix.index[i] for i in indices.flatten()]
recommended_products = get_products_from_similar_users(similar_users)
```

**Why Cosine Similarity?**
- Handles sparse matrices well (most users haven't rated most products)
- Focuses on rating patterns rather than absolute values
- Scale-invariant (works with different rating ranges)

**Why Brute Force Algorithm?**
- Guarantees finding exact nearest neighbors
- Acceptable performance for moderate dataset sizes
- More accurate than approximate methods (ball_tree, kd_tree)

**Interaction Rating Calculation:**

```python
# Favorites are high-value interactions
if interaction_type == 'favorite':
    rating = 5

# Purchases are highest-value interactions
elif interaction_type == 'purchase':
    rating = 5

# Views are low-value interactions
elif interaction_type == 'view':
    rating = 1

# Explicit ratings from reviews
elif interaction_type == 'rating':
    rating = user_provided_rating  # 1-5
```

### 2. Linear Regression (Demand Prediction)

**Purpose:** Forecast future product demand based on historical sales

**Algorithm Details:**

```python
from sklearn.linear_model import LinearRegression

# Step 1: Prepare time series data
x = np.array(range(len(sales_history))).reshape(-1, 1)  # Time periods
y = np.array(sales_history)                              # Sales quantities

# Step 2: Train linear regression model
model = LinearRegression()
model.fit(x, y)

# Step 3: Predict next period
next_period = np.array([[len(sales_history)]])
prediction = model.predict(next_period)[0]

# Step 4: Calculate confidence (R² score)
confidence = model.score(x, y)

# Step 5: Determine trend
trend = "increasing" if prediction > sales_history[-1] else "decreasing"
```

**Model Evaluation Metrics:**

- **R² Score (Coefficient of Determination):**
  - Range: 0 to 1 (higher is better)
  - Interpretation:
    - R² > 0.7: Strong predictive power
    - 0.4 < R² < 0.7: Moderate predictive power
    - R² < 0.4: Weak predictive power

- **Slope (Trend Indicator):**
  - Positive slope: Increasing demand
  - Negative slope: Decreasing demand
  - Magnitude: Rate of change

**Handling Edge Cases:**

```python
# Insufficient data
if len(sales_history) < 2:
    return {
        "prediction": 0,
        "trend": "insufficient_data",
        "confidence": 0
    }

# Constant sales (zero variance)
if np.std(sales_history) == 0:
    return {
        "prediction": sales_history[0],
        "trend": "stable",
        "confidence": 1.0
    }
```

### 3. Engagement Scoring (Trending Analysis)

**Purpose:** Identify products with high recent engagement

**Algorithm Details:**

```python
def calculate_trending_score(product):
    views = product.get('views', 0)
    favorites = product.get('favorites_count', 0)
    purchases = product.get('purchase_count', 0)
    
    # Weighted scoring
    trending_score = (
        views * 1.0 +           # Base engagement
        favorites * 2.0 +       # Intent signal
        purchases * 3.0         # Conversion signal
    )
    
    return trending_score
```

**Weight Rationale:**

- **Views (1x):** Indicates awareness but low commitment
- **Favorites (2x):** Shows intent to purchase later
- **Purchases (3x):** Strongest signal of product desirability

**Time Decay (Future Enhancement):**

```python
# Apply exponential decay based on recency
from datetime import datetime, timedelta

def apply_time_decay(score, created_at, decay_rate=0.1):
    days_old = (datetime.now() - created_at).days
    decay_factor = np.exp(-decay_rate * days_old)
    return score * decay_factor
```

### 4. Category Aggregation

**Purpose:** Identify trending product categories

**Algorithm Details:**

```python
import pandas as pd

# Step 1: Group products by category
category_stats = products_df.groupby('category').agg({
    'views': 'sum',
    'favorites_count': 'sum',
    'id': 'count',
    'price': 'mean'
}).reset_index()

# Step 2: Calculate trending score
category_stats['trending_score'] = (
    category_stats['views'] +
    category_stats['favorites_count'] * 2
)

# Step 3: Sort by trending score
category_stats = category_stats.sort_values(
    'trending_score',
    ascending=False
)
```

### 5. Rule-Based Insights

**Purpose:** Generate actionable recommendations for admins

**Algorithm Details:**

```python
def generate_platform_insights(platform_data):
    insights = []
    
    # User growth analysis
    user_growth_rate = (
        platform_data.newUsersThisMonth / 
        platform_data.totalUsers * 100
    )
    
    if user_growth_rate > 15:
        insights.append(
            f"Strong user growth of {user_growth_rate:.1f}% this month. "
            "Consider scaling infrastructure."
        )
    elif user_growth_rate < 5:
        insights.append(
            f"User growth is {user_growth_rate:.1f}% this month. "
            "Launch marketing campaigns to boost acquisition."
        )
    
    # Shop verification bottleneck detection
    pending_rate = (
        platform_data.pendingShops / 
        platform_data.totalShops * 100
    )
    
    if pending_rate > 20:
        insights.append(
            f"{platform_data.pendingShops} shops ({pending_rate:.1f}%) "
            "are pending verification. Prioritize shop approvals."
        )
    
    # Product quality monitoring
    flagged_rate = (
        platform_data.flaggedProducts / 
        platform_data.totalProducts * 100
    )
    
    if flagged_rate > 3:
        insights.append(
            f"{platform_data.flaggedProducts} products ({flagged_rate:.1f}%) "
            "are flagged. Investigate quality issues."
        )
    
    # Deal activity optimization
    deals_per_shop = (
        platform_data.activeDeals / 
        platform_data.verifiedShops
    )
    
    if deals_per_shop < 0.5:
        insights.append(
            f"Only {deals_per_shop:.2f} deals per verified shop. "
            "Encourage sellers to create more deals."
        )
    
    # User engagement analysis
    active_rate = (
        platform_data.activeUsers / 
        platform_data.totalUsers * 100
    )
    
    if active_rate < 80:
        insights.append(
            f"User engagement is {active_rate:.1f}%. "
            "Send personalized notifications to re-engage users."
        )
    
    return insights[:5]  # Return top 5 insights
```

**Threshold Rationale:**

| Metric | Threshold | Reasoning |
|--------|-----------|-----------|
| User growth | 15% | Industry benchmark for healthy growth |
| Pending shops | 20% | Indicates verification bottleneck |
| Flagged products | 3% | Quality control threshold |
| Deals per shop | 0.5 | Minimum for active marketplace |
| Active users | 80% | Engagement health indicator |

## API Endpoints

### Health & Documentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service information and endpoint list |
| GET | `/health` | Health check with database status |
| GET | `/version` | Version and build information |
| GET | `/docs` | Interactive Swagger UI documentation |
| GET | `/redoc` | ReDoc API documentation |

### Recommendations

#### Get Product Recommendations

```http
GET /recommendations/products?user_id=1&top_n=5
```

**Query Parameters:**
- `user_id` (required): User ID for personalized recommendations
- `top_n` (optional, default: 5): Number of recommendations to return

**Response:**
```json
{
  "user_id": 1,
  "recommendations": [
    {
      "product_id": "uuid",
      "name": "Product Name",
      "category": "Electronics",
      "price": 29.99
    }
  ],
  "method": "collaborative_filtering",
  "similar_users_count": 5
}
```

**Methods:**
- `collaborative_filtering` - KNN-based user similarity
- `popular_products` - Fallback for new users or insufficient data

### Demand Prediction

#### Predict Product Demand

```http
POST /demand/predict
GET /demand/predict?product_id=uuid&days=7
```

**Query Parameters:**
- `product_id` (optional): Specific product to predict (omit for all products)
- `days` (optional, default: 7): Prediction period

**Response:**
```json
{
  "predictions": [
    {
      "product_id": "uuid",
      "product_name": "Product Name",
      "current_sales": 150,
      "predicted_demand": 175.5,
      "trend": "increasing",
      "confidence": 0.85,
      "historical_data_points": 30,
      "prediction_period_days": 7
    }
  ],
  "model": "linear_regression",
  "total_products": 10
}
```

**Trend Values:**
- `increasing` - Demand is rising
- `decreasing` - Demand is falling
- `stable` - Demand is constant
- `insufficient_data` - Not enough historical data

### Trending Analysis

#### Get Trending Products

```http
GET /trending/products?limit=10&category=Electronics
```

**Query Parameters:**
- `limit` (optional, default: 5): Number of products to return
- `category` (optional): Filter by category

**Response:**
```json
{
  "trending_products": [
    {
      "product_id": "uuid",
      "name": "Product Name",
      "category": "Electronics",
      "price": 49.99,
      "views": 1500,
      "favorites": 250,
      "purchases": 75,
      "trending_score": 2475,
      "average_rating": 4.5
    }
  ],
  "method": "engagement_analysis",
  "total": 50,
  "category_filter": "Electronics"
}
```

#### Get Trending Categories

```http
GET /trending/categories
```

**Response:**
```json
{
  "trending_categories": [
    {
      "category": "Electronics",
      "total_views": 15000,
      "total_favorites": 2500,
      "product_count": 120,
      "avg_price": 45.99,
      "trending_score": 20000
    }
  ],
  "method": "category_aggregation",
  "total_categories": 10
}
```

### Admin Insights

#### Generate Platform Insights

```http
POST /insights/generate
```

**Request Body:**
```json
{
  "platformData": {
    "totalUsers": 10000,
    "activeUsers": 8500,
    "totalShops": 500,
    "verifiedShops": 450,
    "pendingShops": 40,
    "rejectedShops": 10,
    "totalProducts": 5000,
    "flaggedProducts": 50,
    "activeDeals": 200,
    "newUsersThisMonth": 1200,
    "dealsThisMonth": 50
  }
}
```

**Response:**
```json
{
  "success": true,
  "insights": [
    "Strong user growth of 12.0% this month. Consider scaling infrastructure.",
    "User engagement is 85.0%. Platform health is good.",
    "Only 0.44 deals per verified shop. Encourage sellers to create more deals.",
    "Low flagged product rate (1.0%). Product quality monitoring is effective.",
    "Platform metrics are healthy. Continue monitoring KPIs."
  ],
  "method": "rule_based_analysis"
}
```

## Recommendation Engine

### Collaborative Filtering Implementation

**File:** `app/routers/recommendations.py`

**Core Function:**

```python
def build_recommendation_model(interactions_data, products_data):
    """
    Build collaborative filtering model from user interaction data.
    
    Args:
        interactions_data: List of user-product interactions
        products_data: List of product records
    
    Returns:
        model: Trained KNN model
        user_product_matrix: Pivot table of user-product ratings
    """
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
```

**Recommendation Generation:**

```python
# Get user's vector
user_idx = user_product_matrix.index.get_loc(user_id)
user_vector = user_product_matrix.iloc[user_idx].values.reshape(1, -1)

# Find similar users
distances, indices = model.kneighbors(user_vector, n_neighbors=6)

# Get products already rated by user
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
    recommended.extend(new_products)
```

**Cold Start Problem Handling:**

```python
# New user (no interactions)
if user_id not in user_product_matrix.index:
    # Return popular products
    sorted_products = sorted(
        products_data,
        key=lambda x: x.get('views', 0) + x.get('favorites_count', 0) * 2,
        reverse=True
    )[:top_n]
    
    return {
        "recommendations": sorted_products,
        "method": "popular_products",
        "note": "New user, showing popular products"
    }
```

## Demand Prediction System

### Linear Regression Implementation

**File:** `app/routers/demand.py`

**Core Function:**

```python
def predict_demand(sales_history: list) -> dict:
    """
    Predict future demand using linear regression.
    
    Args:
        sales_history: List of historical sales quantities
    
    Returns:
        dict: Prediction, trend, confidence, and slope
    """
    # Prepare data
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
```

**Sales Data Aggregation:**

```python
# Convert sale_date to datetime
df['sale_date'] = pd.to_datetime(df['sale_date'])

# Group by product and date, sum quantities
daily_sales = df.groupby([
    'product_id',
    pd.Grouper(key='sale_date', freq='D')
])['quantity'].sum().reset_index()

# Get sales history for specific product
product_sales = daily_sales[daily_sales['product_id'] == product_id]
sales_history = product_sales.sort_values('sale_date')['quantity'].tolist()
```

## Trending Analysis

### Engagement Scoring Implementation

**File:** `app/routers/trending.py`

**Product Trending Score:**

```python
def calculate_trending_score(product):
    views = product.get("views", 0)
    favorites = product.get("favorites_count", 0)
    purchases = product.get("purchase_count", 0)
    
    trending_score = views + (favorites * 2) + (purchases * 3)
    
    return {
        "product_id": product["id"],
        "name": product.get("name", "Unknown"),
        "category": product.get("category", "General"),
        "price": product.get("price", 0),
        "views": views,
        "favorites": favorites,
        "purchases": purchases,
        "trending_score": trending_score,
        "average_rating": product.get("average_rating", 0)
    }
```

**Category Trending Score:**

```python
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
category_stats = category_stats.sort_values(
    "trending_score",
    ascending=False
)
```

## Admin Insights Generator

### Rule-Based Analytics Implementation

**File:** `app/routers/insights.py`

**Insight Generation Logic:**

```python
def generate_platform_insights(data: PlatformData) -> List[str]:
    insights = []
    
    # 1. User Growth Analysis
    user_growth_rate = (
        data.newUsersThisMonth / data.totalUsers * 100
    ) if data.totalUsers > 0 else 0
    
    if user_growth_rate > 15:
        insights.append(
            f"Strong user growth of {user_growth_rate:.1f}% this month. "
            "Consider scaling infrastructure and support resources."
        )
    elif user_growth_rate < 5:
        insights.append(
            f"User growth is {user_growth_rate:.1f}% this month. "
            "Launch marketing campaigns or referral programs."
        )
    
    # 2. Shop Verification Analysis
    pending_rate = (
        data.pendingShops / data.totalShops * 100
    ) if data.totalShops > 0 else 0
    
    if pending_rate > 20:
        insights.append(
            f"{data.pendingShops} shops ({pending_rate:.1f}%) "
            "are pending verification. Prioritize shop approvals."
        )
    
    # 3. Product Quality Analysis
    flagged_rate = (
        data.flaggedProducts / data.totalProducts * 100
    ) if data.totalProducts > 0 else 0
    
    if flagged_rate > 3:
        insights.append(
            f"{data.flaggedProducts} products ({flagged_rate:.1f}%) "
            "are flagged. Investigate quality issues."
        )
    
    # 4. Deal Activity Analysis
    deals_per_shop = (
        data.activeDeals / data.verifiedShops
    ) if data.verifiedShops > 0 else 0
    
    if deals_per_shop < 0.5:
        insights.append(
            f"Only {deals_per_shop:.2f} deals per verified shop. "
            "Encourage sellers to create more deals."
        )
    
    # 5. User Engagement Analysis
    active_rate = (
        data.activeUsers / data.totalUsers * 100
    ) if data.totalUsers > 0 else 0
    
    if active_rate < 80:
        insights.append(
            f"User engagement is {active_rate:.1f}%. "
            "Send personalized notifications to re-engage users."
        )
    
    # Ensure minimum 5 insights
    if len(insights) < 5:
        insights.append(
            "Platform metrics are healthy. "
            "Continue monitoring key performance indicators."
        )
    
    return insights[:5]
```

## Database Integration

### Supabase Client Configuration

**File:** `app/database.py`

**Client Initialization:**

```python
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

### Data Fetching Functions

**Get User Interactions:**

```python
def get_user_interactions() -> List[Dict]:
    """
    Fetch user interaction data from Supabase.
    Tries user_interactions table first, falls back to favorites.
    """
    try:
        # Primary source
        response = supabase.table("user_interactions").select("*").execute()
        
        if response.data and len(response.data) > 0:
            return response.data
        
        # Fallback to favorites
        favorites_response = supabase.table("favorites").select(
            "user_id, product_id"
        ).execute()
        
        if favorites_response.data:
            # Convert favorites to interaction format
            interactions = []
            for fav in favorites_response.data:
                interactions.append({
                    "user_id": fav["user_id"],
                    "product_id": fav["product_id"],
                    "rating": 5,  # Favorites = high rating
                    "interaction_type": "favorite"
                })
            return interactions
        
        return []
    except Exception as e:
        print(f"Error fetching user interactions: {e}")
        return []
```

**Get Products:**

```python
def get_products() -> List[Dict]:
    """
    Fetch all products from Supabase.
    """
    try:
        response = supabase.table("products").select("*").execute()
        
        if response.data and len(response.data) > 0:
            return response.data
        
        return []
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []
```

**Get Sales Data:**

```python
def get_sales_data() -> List[Dict]:
    """
    Fetch sales data from Supabase.
    Tries sales table first, falls back to orders.
    """
    try:
        # Primary source
        response = supabase.table("sales").select("*").execute()
        
        if response.data and len(response.data) > 0:
            return response.data
        
        # Fallback to orders
        orders_response = supabase.table("orders").select("*").execute()
        
        if orders_response.data:
            return orders_response.data
        
        return []
    except Exception as e:
        print(f"Error fetching sales data: {e}")
        return []
```

**Health Check:**

```python
def health_check() -> Dict:
    """
    Check database connection health.
    """
    try:
        # Test query
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
```

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Supabase account and project
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd zniyerbuy-ai-module
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the root directory:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key

# CORS Configuration (optional)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000

# Debug Mode (optional)
DEBUG=false
```

5. **Start the development server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

6. **Verify installation**

Visit `http://localhost:8000/health` - should return:
```json
{
  "service": "ZniyerBuy AI Module",
  "status": "healthy",
  "version": "1.0.0",
  "database": {
    "status": "connected",
    "database": "supabase"
  }
}
```

7. **Access API documentation**

Visit `http://localhost:8000/docs` for interactive Swagger UI

### Production Deployment

1. **Install production server**
```bash
pip install gunicorn
```

2. **Run with Gunicorn**
```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

3. **Configure systemd service** (Linux)

Create `/etc/systemd/system/zniyerbuy-ai.service`:

```ini
[Unit]
Description=ZniyerBuy AI Module
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/zniyerbuy-ai-module
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

4. **Enable and start service**
```bash
sudo systemctl enable zniyerbuy-ai
sudo systemctl start zniyerbuy-ai
```

5. **Configure reverse proxy** (Nginx)

```nginx
server {
  listen 80;
  server_name ai.zniyerbuy.com;
  
  location / {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
  }
}
```

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SUPABASE_URL` | Yes | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Yes | Supabase anon or service key | `eyJhbGc...` |
| `ALLOWED_ORIGINS` | No | CORS allowed origins (comma-separated) | `http://localhost:3000` |
| `DEBUG` | No | Enable debug mode | `true` or `false` |

## API Documentation

### Interactive Documentation

**Swagger UI:** `http://localhost:8000/docs`

**ReDoc:** `http://localhost:8000/redoc`

### Response Format

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "method": "algorithm_name"
}
```

**Error Response:**
```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

### Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Database connection failed |

## Performance Optimization

### Caching Strategy

**Future Enhancement:**

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache product data for 5 minutes
@lru_cache(maxsize=128)
def get_cached_products(cache_key: str):
    return get_products()

# Invalidate cache every 5 minutes
cache_key = datetime.now().strftime("%Y%m%d%H%M") // 5
products = get_cached_products(cache_key)
```

### Database Query Optimization

**Batch Fetching:**

```python
# Fetch all required data in parallel
import asyncio

async def fetch_all_data():
    tasks = [
        fetch_products(),
        fetch_interactions(),
        fetch_sales()
    ]
    return await asyncio.gather(*tasks)
```

**Selective Field Fetching:**

```python
# Only fetch required fields
response = supabase.table("products").select(
    "id, name, category, price, views, favorites_count"
).execute()
```

### Model Optimization

**Incremental Training:**

```python
# Update model with new data instead of full retrain
def update_model_incremental(model, new_interactions):
    # Add new interactions to existing matrix
    # Retrain only affected user vectors
    pass
```

**Model Persistence:**

```python
import pickle

# Save trained model
with open('recommendation_model.pkl', 'wb') as f:
    pickle.dump(model, f)

# Load trained model
with open('recommendation_model.pkl', 'rb') as f:
    model = pickle.load(f)
```

---

**Version:** 1.0.0  
**Last Updated:** 2026-06-13  
**Maintained By:** ZniyerBuy Development Team
