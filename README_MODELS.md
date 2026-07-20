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
