# 🤖 ZNIYERBUY AI Module

A Python microservice that powers ZNIYERBUY's AI features: personalized product recommendations, trending products/categories, and live per-shop revenue/traffic predictions for the seller Analytics dashboard. Built with **FastAPI**, reading directly from the same **Supabase Postgres** database as the Node.js backend.

This README is written directly from the source in `app/routers/` and `app/services/` — it reflects exactly what's implemented today, including which features are still stubs.

---

## Table of Contents
- [Core Features](#core-features)
- [What's a Stub vs. Fully Implemented](#whats-a-stub-vs-fully-implemented)
- [Live Shop Predictions](#live-shop-predictions)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)

---

## Core Features

1. **Personalized Recommendations** (`/recommendations/products`) — ranks candidate products against a customer's `user_interests` categories and favorited products, combined with each product's own engagement signals (`recommendation_score`, `average_rating`, `favorites_count`). Falls back to general top-quality products for anonymous/cold-start users. This is a **rule-based scoring model**, not a trained ML model.

2. **Trending Analysis** (`/trending/products`, `/trending/categories`) — computed live from `user_interactions`, weighted by action type and recency (`?days=`), with a fallback to all-time engagement metrics when there isn't enough recent activity.

3. **Live Shop Predictions** (`/predictions/shop/{shop_id}`) — next-month revenue, daily revenue, expected users, top category, a 30-day forecast, and category outlook, computed fresh from each shop's real Supabase orders/products on every request (no pre-trained model, no offline training step).

4. **Demand Prediction** (`/demand`) — **placeholder only**, see below.

5. **Admin Insights** (`/insights`) — **placeholder only**, see below.

## What's a Stub vs. Fully Implemented

`main.py` imports five routers. Two of them are currently placeholders so the service can boot without `ImportError`s:

| Router | Status | Detail |
|--------|--------|--------|
| `recommendations` | ✅ Implemented | Rule-based scoring against `user_interests` + favorites + engagement metrics |
| `trending` | ✅ Implemented | Recency/action-weighted scoring over `user_interactions` |
| `predictions` | ✅ Implemented | 6 predictor services aggregated per shop (see below) |
| `demand` | 🚧 Stub | `GET /demand/` returns `{"status": "not_implemented", ...}` — replace `app/routers/demand.py` with a real implementation |
| `insights` | 🚧 Stub | `GET /insights/` returns `{"status": "not_implemented", ...}` — replace `app/routers/insights.py` with a real implementation |

There is **no scikit-learn model (KNN, regression, etc.) currently wired into any router** despite `scikit-learn` being a listed dependency — recommendations and trending are rule-based/statistical, not trained ML models, and demand/insights (where regression-based forecasting was originally planned) are unimplemented stubs.

## Live Shop Predictions

Powers the seller Analytics page's "AI-Powered Predictions for Next Month" section via `GET /predictions/shop/{shop_id}`.

Each prediction lives in its own file under `app/services/`, built from a shop's real order/product history — no pre-trained model, no external dataset. Numbers update on every request:

| # | Prediction | File | Method |
|---|---|---|---|
| 1 | Predicted Revenue (next month total) | `revenue_predictor.py` | Sum of the 30-day forecast |
| 2 | Daily Revenue (average per day) | `daily_revenue_avg.py` | Average of the 30-day forecast |
| 3 | Expected Users | `user_traffic_predictor.py` | Trailing 30-day distinct customers × clamped growth rate |
| 4 | Next Month Top Category | `top_category_classifier.py` | Top row of the category outlook |
| 5 | Daily Revenue Forecast (30-day series) | `daily_revenue_forecast.py` | Daily bucketing → 7-day rolling mean → linear trend → clamped growth |
| 6 | Category Sales Prediction | `category_sales_prediction.py` | Catalog composition + engagement (views/favorites/recommendation_score), labeled `catalog_engagement_proxy` |

All six are combined by `predictions_aggregator.py` into the single response returned by the endpoint.

## System Architecture

```
                Node.js Backend (zniyerbuy-backend)
                       │  GET/POST (server-to-server, no auth header required
                       │  on this service itself — access control happens
                       │  in the Node backend before it proxies the call)
                       ▼
        ┌───────────────────────────────────────────┐
        │   FastAPI app (main.py)                   │
        │   CORS (GET/POST only) → request logging  │
        │   → routers: recommendations, demand,     │
        │     trending, insights, predictions       │
        └───────────────┬───────────────────────────┘
                        │
                        ▼
              app/database.py (Supabase Python client)
                        │
                        ▼
             PostgreSQL (Supabase) — same DB as the Node backend
```

Clients (mobile app, shop web) never call this service directly — they call the Node.js backend's `/api/v1/ai/*` routes, which proxy to this service.

## Technology Stack

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.139.2 | Web framework |
| uvicorn | 0.51.0 | ASGI server |
| supabase (python) | 2.31.0 | Database access |
| pandas | 3.0.3 | Data wrangling for predictions |
| numpy | 2.5.1 | Numeric computation |
| scikit-learn | 1.9.0 | Listed dependency — not currently used by any implemented router |
| scipy | 1.18.0 | Listed dependency |
| matplotlib | 3.11.1 | Used in the validation notebook, not the API |
| python-dotenv | 1.2.2 | Loads `.env` |
| pydantic | 2.13.4 | Request/response models |

Python 3.11+ recommended.

## Project Structure

```
zniyerbuy-ai-module/
├── main.py                              ← FastAPI app, CORS, logging middleware, router registration
├── app/
│   ├── database.py                      ← Supabase client + data-fetch helpers
│   ├── routers/
│   │   ├── recommendations.py           ← GET /recommendations/products
│   │   ├── trending.py                  ← GET /trending/products, /trending/categories
│   │   ├── predictions.py               ← GET /predictions/shop/{shop_id}
│   │   ├── demand.py                    ← stub
│   │   └── insights.py                  ← stub
│   └── services/
│       ├── recommendations_engine.py
│       ├── trending_engine.py
│       ├── revenue_predictor.py
│       ├── daily_revenue_avg.py
│       ├── daily_revenue_forecast.py
│       ├── user_traffic_predictor.py
│       ├── top_category_classifier.py
│       ├── category_sales_prediction.py
│       ├── predictions_aggregator.py
│       └── shared.py
├── notebooks/
│   └── 00_validate_predictions.ipynb    ← sanity-checks the prediction models against real data
├── requirements.txt
└── .env
```

## API Reference

Base URL: `http://localhost:8000`. Interactive docs auto-generated at **`/docs`** (Swagger) and **`/redoc`**.

| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| GET | `/` | ✅ | Service info + endpoint map |
| GET | `/health` | ✅ | Service + database connectivity check |
| GET | `/version` | ✅ | Version info |
| GET | `/recommendations/products` | ✅ | `?user_id&top_n` — personalized recommendations |
| GET | `/trending/products` | ✅ | `?limit&days` — trending products |
| GET | `/trending/categories` | ✅ | `?limit&days` — trending categories |
| GET | `/predictions/shop/{shop_id}` | ✅ | Combined revenue/traffic/category prediction for a shop |
| GET | `/demand/` | 🚧 | Returns `{"status": "not_implemented"}` |
| GET | `/insights/` | 🚧 | Returns `{"status": "not_implemented"}` |

CORS is restricted to `GET` and `POST` methods only, configured via `ALLOWED_ORIGINS`.

## Installation & Setup

```bash
git clone https://github.com/ShehanRanasinghe/zniyerbuy-ai-module.git
cd zniyerbuy-ai-module

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env          # or create .env manually, see below

uvicorn main:app --reload --port 8000
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Environment Variables

```env
# Supabase connection (required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key

# Comma-separated list of allowed frontend/backend origins.
# Use "*" only for local development.
ALLOWED_ORIGINS=http://localhost:5000,http://localhost:3000,http://localhost:3001

# Set to "true" to include exception details in error responses (dev only)
DEBUG=false
```

---

## Roadmap / Known Gaps

- Implement `app/routers/demand.py` with real demand forecasting (originally planned as historical-sales regression).
- Implement `app/routers/insights.py` with real rule-based or ML-driven admin insights.
- If collaborative-filtering/KNN-based recommendations are still desired, they are not yet built — current recommendations are rule-based on category interest + engagement score, not `scikit-learn` model inference.

For the full project context (all six ZNIYERBUY repos, database schema, sprint history), see `zniyerbuy-project-hub`.