# 🤖 ZniyerBuy AI Module

An intelligent recommendation and analytics microservice powered by machine learning. It provides personalized product recommendations, demand predictions, trending category/product insights, admin insights, and **live per-shop next-month predictions** for the ZniyerBuy marketplace.

---

## 📋 Table of Contents
- [Core Features](#-core-features)
- [Live Shop Predictions](#-live-shop-predictions)
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

5. **Live Shop Predictions**
   - Next-month revenue, daily revenue, expected users, top category, a 30-day forecast, and category outlook — computed fresh from each shop's real Supabase orders/products on every request. See below.

---

## 🔮 Live Shop Predictions

Powers the seller Analytics page's "AI-Powered Predictions for Next Month" section via `GET /predictions/shop/{shop_id}`.

Each prediction lives in its own file under `app/services/`, built from a shop's real order/product history — **no pre-trained model, no external dataset, no training step**. Numbers update every time the endpoint is called.

| # | Prediction | File | Method |
|---|---|---|---|
| 1 | Predicted Revenue (next month total) | `app/services/revenue_predictor.py` | Sum of the 30-day forecast |
| 2 | Daily Revenue (average per day) | `app/services/daily_revenue_avg.py` | Average of the 30-day forecast |
| 3 | Expected Users | `app/services/user_traffic_predictor.py` | Trailing 30-day distinct customers × clamped growth rate |
| 4 | Next Month Top Category | `app/services/top_category_classifier.py` | Top row of the category outlook |
| 5 | Daily Revenue Forecast (30-day series) | `app/services/daily_revenue_forecast.py` | Daily bucketing → 7-day rolling mean → linear trend → clamped growth |
| 6 | Category Sales Prediction | `app/services/category_sales_prediction.py` | Catalog composition + engagement (views/favorites/recommendation_score), labeled `catalog_engagement_proxy` |

`app/services/shared.py` holds the common date/math helpers (used by every module above); `app/services/predictions_aggregator.py` combines all 6 into the API response.

**Why no ML model files:** the previous version of this module trained 6 scikit-learn/statsmodels models on the public Instacart grocery dataset (`legacy/notebooks/`, `legacy/models/`). That dataset has no concept of "shop," predicts among 21 grocery departments unrelated to real marketplace categories, and produced one static number shared by every shop on the platform. The current approach computes directly from each shop's own data instead. For shops with thin order history, predictions fall back to a flat/naive projection (`confidence: "low"`) rather than fabricating a trend, and shops under 3 orders get `status: "no_data"` instead of a guess.

**Validating it:** `notebooks/00_validate_predictions.ipynb` imports the 6 modules directly and checks them against synthetic data plus (optionally) a real `shop_id`. Run it any time you touch `app/services/`.

---

## 🏗️ System Architecture
```text
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
│  │   - /predictions                  │  │
│  └───────────────────────────────────┘  │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│      app/services/ (live predictions)   │ 
│ ┌───────────────────────────────────┐   │
│ │ revenue_predictor.py              │   │
│ │ daily_revenue_avg.py              │   │
│ │ daily_revenue_forecast.py         │   │
│ │ user_traffic_predictor.py         │   │
│ │ top_category_classifier.py        │   │
│ │ category_sales_prediction.py      │   │
│ │ predictions_aggregator.py         │   │
│ └───────────────────────────────────┘   │
│ + Scikit-Learn (recommendations/demand) │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│         Supabase Database               │
│  - User interactions & views            │
│  - Product catalog                      │
│  - Orders (per-shop revenue history)    │
└─────────────────────────────────────────┘
```
---

## 🛠️ Technology Stack
- **Framework:** FastAPI (Uvicorn ASGI)
- **Database Client:** Supabase SDK
- **Data Manipulation:** Pandas, NumPy
- **Machine Learning:** Scikit-Learn (recommendations & demand only)

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

### 5. Validating the Prediction Modules
No dataset download or training step needed. Run the validation notebook:
```bash
jupyter notebook notebooks/00_validate_predictions.ipynb
```

*Note: `legacy/notebooks/`, `legacy/models/`, and `legacy/verify_models.py` contain the previous Instacart-trained approach, kept for reference only and no longer used by the running app.*

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
| `/predictions/shop/{shop_id}` | `GET` | Live next-month predictions for one shop (revenue, daily revenue, users, top category, 30-day forecast, category outlook) |

---
**Version:** 1.1.0  
**Maintained By:** ZniyerBuy Development Team
