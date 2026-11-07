# 🤖 ZniyerBuy AI Module

An intelligent recommendation and analytics microservice powered by machine learning. It provides personalized product recommendations, demand predictions, trending category/product insights, and predictive forecasting for the ZniyerBuy marketplace.

---

## 📋 Table of Contents
- [Core Features](#-core-features)
- [Machine Learning & Prediction Models](#-machine-learning--prediction-models)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Installation & Setup](#-installation--setup)
- [API Documentation](#-api-documentation)

---

## ✨ Core Features

1. **Personalized Recommendations**
   - Collaborative filtering (K-Nearest Neighbors) matching users based on interaction profiles.
   - Smart fallbacks to platform-wide popular products for cold-start (new) users.

2. **Demand Prediction**
   - Real-time product demand forecasting using historical sales regressions.

3. **Trending Analysis**
   - Real-time multi-factor product and category ranking based on user views, favorites, and conversions.

4. **Automated Admin Insights**
   - Rule-based analytics generating actionable recommendations regarding seller onboarding, quality issues, and user engagement.

---

## 🧠 Machine Learning & Prediction Models

The AI module uses **6 dedicated ML models** to generate forecasts for the dashboard:

| # | Model File | Notebook | Algorithm | Target |
|---|---|---|---|---|
| 1 | `revenue_predictor.pkl` | `01_revenue_prediction.ipynb` | Random Forest Regressor | Next month total revenue (Rs.) |
| 2 | `daily_revenue_predictor.pkl` | `02_daily_revenue_avg.ipynb` | Gradient Boosting Regressor | Average daily revenue (Rs.) |
| 3 | `user_traffic_predictor.pkl` | `03_user_traffic_prediction.ipynb` | Ridge Regression + Polynomials | Expected active users next month |
| 4 | `top_category_classifier.pkl` | `04_top_category_classifier.ipynb` | Random Forest Classifier | Top category by revenue |
| 5 | `daily_revenue_forecast.pkl` | `05_daily_revenue_forecast.ipynb` | ARIMA(5,1,2) | 30-day forecasted daily revenue |
| 6 | `category_sales_predictor.pkl` | `06_category_sales_prediction.ipynb` | Multi-Output Random Forest | Next month sales across 21 categories |

*Note: Since the raw dataset has no pricing, revenue models use a deterministic average price proxy per department (e.g. Produce = Rs. 150, Dairy = Rs. 300, Meat = Rs. 700).*

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌───────────────────────────────────┐  │
│  │   CORS / Request Logging          │  │
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
│  │   Scikit-Learn Models & ARIMA     │  │
│  └───────────────────────────────────┘  │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│         Supabase Database               │
│  - User interactions & views            │
│  - Product catalog & sales history      │
└─────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack
- **Framework:** FastAPI (Uvicorn ASGI)
- **Database Client:** Supabase SDK
- **Data Manipulation:** Pandas, NumPy
- **Machine Learning:** Scikit-Learn, Statsmodels, Joblib

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.8+
- Active Supabase Project

### 2. Set Up the Project
```bash
# Clone the repository
git clone <repository-url>
cd zniyerbuy-ai-module

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root folder:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000
```

### 4. Running the Dev Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Verify the server status at `http://localhost:8000/health`.

### 5. Running Model Training & Verification
Training notebooks are located in the `notebooks/` directory. Run them sequentially (`00` to `06`) inside Jupyter:
```bash
jupyter notebook notebooks/
```
Verify that all serialized models are loaded and functioning correctly:
```bash
python verify_models.py
```

---

## 📡 API Documentation

Interactive API documents are served directly by FastAPI:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Summary of Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Service status and database connectivity check |
| `/recommendations` | `POST` | Generates user-based recommendation lists |
| `/demand` | `POST` | Forecasts unit demand over a specified period |
| `/trending/products` | `GET` | Returns top-performing products by engagement score |
| `/trending/categories` | `GET` | Returns top-performing categories by engagement score |
| `/insights` | `GET` | Generates diagnostic insights for administrators |

---
**Version:** 1.0.0  
**Maintained By:** ZniyerBuy Development Team
