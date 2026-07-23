"""
app/services/shared.py
-----------------------
What: Generic, reusable numerical/date helpers shared by every prediction
      module (revenue_predictor, daily_revenue_avg, daily_revenue_forecast,
      user_traffic_predictor, top_category_classifier, category_sales_prediction).
Why:  Keeps the actual time-series math (date parsing, daily bucketing,
      rolling mean, linear regression) in ONE place so every predictor
      behaves consistently — while each predictor file still owns its own
      business logic and thresholds independently.
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional, Callable
import numpy as np

FORECAST_DAYS = 30
GROWTH_CLAMP_MIN = -0.40   # never predict a >40% monthly decline
GROWTH_CLAMP_MAX = 0.60    # never predict a >60% monthly spike


def parse_dt(value) -> Optional[datetime]:
    """Parse Supabase's ISO timestamp strings (with or without timezone)."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        s = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def non_cancelled(orders: List[Dict]) -> List[Dict]:
    """Filter out cancelled orders — every predictor should call this first."""
    return [o for o in orders if (o.get("status") or "").lower() != "cancelled"]


def order_date_range(orders: List[Dict]):
    """Returns (first_day, last_day, history_days) or None if no valid dates."""
    dates = [d.date() for d in (parse_dt(o.get("created_at")) for o in orders) if d]
    if not dates:
        return None
    first_day, last_day = min(dates), max(dates)
    return first_day, last_day, (last_day - first_day).days + 1


def daily_series(records: List[Dict], value_fn: Callable[[list], float], first_day, last_day) -> List[float]:
    """
    Bucket records into a continuous daily series between first_day and
    last_day inclusive (missing days become 0 via value_fn([])).
    """
    n_days = (last_day - first_day).days + 1
    buckets: List[list] = [[] for _ in range(n_days)]
    for r in records:
        dt = parse_dt(r.get("created_at"))
        if not dt:
            continue
        idx = (dt.date() - first_day).days
        if 0 <= idx < n_days:
            buckets[idx].append(r)
    return [value_fn(b) for b in buckets]


def rolling_mean(series: List[float], window: int) -> List[float]:
    if len(series) < window:
        return series[:]
    arr = np.array(series, dtype=float)
    kernel = np.ones(window) / window
    smoothed = np.convolve(arr, kernel, mode="valid")
    return smoothed.tolist()


def linear_trend(y: List[float]):
    """Fit y = a + b*x over x = 0..n-1. Returns (intercept, slope, r2)."""
    n = len(y)
    if n < 2:
        return (y[0] if n else 0.0), 0.0, 0.0
    x = np.arange(n, dtype=float)
    y_arr = np.array(y, dtype=float)
    if np.allclose(y_arr, y_arr[0]):
        return float(y_arr[0]), 0.0, 0.0
    b, a = np.polyfit(x, y_arr, 1)
    pred = a + b * x
    ss_res = np.sum((y_arr - pred) ** 2)
    ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return float(a), float(b), float(max(0.0, r2))


def customer_id(order: Dict) -> str:
    """Best-effort unique customer identifier from an order record."""
    return str(order.get("customer_phone") or order.get("customer_name") or order.get("id"))