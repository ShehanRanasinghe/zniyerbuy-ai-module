"""
verify_models.py
----------------
What: Load all 6 saved .pkl models and run sample predictions
Why:  Quick sanity check after training — confirm all models exist and infer correctly
Method: joblib.load each file, predict with dummy/last-known input, print result
"""

import joblib
import numpy as np
import os

MODELS_PATH = 'models'

# Colour codes for terminal output
GREEN  = '\033[92m'
RED    = '\033[91m'
YELLOW = '\033[93m'
RESET  = '\033[0m'
BOLD   = '\033[1m'

def check(label, passed, detail=''):
    status = f'{GREEN}✅ PASS{RESET}' if passed else f'{RED}❌ FAIL{RESET}'
    print(f'  {status}  {label}')
    if detail:
        print(f'         {YELLOW}{detail}{RESET}')

print(f'\n{BOLD}=== ZniyerBuy ML Model Verification ==={RESET}\n')

# ─── 1. Revenue Predictor ─────────────────────────────────────────────────────
print(f'{BOLD}[1] revenue_predictor.pkl{RESET}')
try:
    model = joblib.load(f'{MODELS_PATH}/revenue_predictor.pkl')
    # Features: total_orders, total_items, unique_users, avg_reorder,
    #           items_per_order, prev_revenue, prev_orders, prev_users, revenue_growth
    sample = [[500, 3200, 180, 0.65, 6.4, 850000, 480, 170, 0.05]]
    pred = model.predict(sample)[0]
    check('Model loads',   True)
    check('Inference runs', True, f'Predicted Revenue: Rs. {pred:,.2f}')
except Exception as e:
    check('revenue_predictor.pkl', False, str(e))

print()

# ─── 2. Daily Revenue Predictor ───────────────────────────────────────────────
print(f'{BOLD}[2] daily_revenue_predictor.pkl{RESET}')
try:
    model = joblib.load(f'{MODELS_PATH}/daily_revenue_predictor.pkl')
    # Features: order_dow, monthly_order_count, monthly_item_count, avg_reorder,
    #           avg_hour, items_per_order, prev_same_dow_revenue, revenue_growth_dow
    sample = [[3, 420, 2700, 0.62, 13.5, 6.4, 27000, 0.03]]
    pred = model.predict(sample)[0]
    check('Model loads',   True)
    check('Inference runs', True, f'Avg Daily Revenue: Rs. {pred:,.2f}')
except Exception as e:
    check('daily_revenue_predictor.pkl', False, str(e))

print()

# ─── 3. User Traffic Predictor ────────────────────────────────────────────────
print(f'{BOLD}[3] user_traffic_predictor.pkl{RESET}')
try:
    model = joblib.load(f'{MODELS_PATH}/user_traffic_predictor.pkl')
    # Features: prev_users, prev_prev_users, user_growth_rate, rolling_avg_3m,
    #           prev_orders, avg_days_between, orders_per_user
    sample = [[1100, 980, 0.12, 1040, 520, 11.2, 2.3]]
    pred = int(model.predict(sample)[0])
    check('Model loads (Pipeline)',  True)
    check('Inference runs',          True, f'Expected Users: {pred:,}')
except Exception as e:
    check('user_traffic_predictor.pkl', False, str(e))

print()

# ─── 4. Top Category Classifier ───────────────────────────────────────────────
print(f'{BOLD}[4] top_category_classifier.pkl{RESET}')
try:
    bundle = joblib.load(f'{MODELS_PATH}/top_category_classifier.pkl')
    feature_cols = bundle['feature_cols']
    # Create a zero feature vector (neutral input)
    sample = np.zeros((1, len(feature_cols)))
    pred_label   = bundle['model'].predict(sample)[0]
    pred_dept_id = int(bundle['label_encoder'].inverse_transform([pred_label])[0])
    dept_name    = bundle['dept_map'].get(pred_dept_id, f'dept_{pred_dept_id}')
    prob         = bundle['model'].predict_proba(sample).max()
    check('Bundle loads (model + encoder)',  True)
    check('Inference runs',                 True, f"Top Category: {dept_name.title()} (conf: {prob*100:.1f}%)")
except Exception as e:
    check('top_category_classifier.pkl', False, str(e))

print()

# ─── 5. Daily Revenue Forecast ────────────────────────────────────────────────
print(f'{BOLD}[5] daily_revenue_forecast.pkl{RESET}')
try:
    bundle = joblib.load(f'{MODELS_PATH}/daily_revenue_forecast.pkl')
    forecast = bundle['forecast_30_days']
    avg_d    = bundle['avg_daily']
    total    = bundle['total_forecast']
    check('Bundle loads (ARIMA result + forecast)',  True)
    check('30-day forecast array valid',
          len(forecast) == 30, f'Days: {len(forecast)} | Avg: Rs. {avg_d:,.2f} | Total: Rs. {total:,.2f}')
except Exception as e:
    check('daily_revenue_forecast.pkl', False, str(e))

print()

# ─── 6. Category Sales Predictor ──────────────────────────────────────────────
print(f'{BOLD}[6] category_sales_predictor.pkl{RESET}')
try:
    bundle = joblib.load(f'{MODELS_PATH}/category_sales_predictor.pkl')
    next_preds = bundle['next_month_pred']   # pre-computed dict
    dept_map   = bundle['departments']
    top_col    = max(next_preds, key=next_preds.get)
    top_id     = int(top_col.split('_')[1])
    top_name   = dept_map.get(top_id, f'dept_{top_id}')
    top_units  = int(next_preds[top_col])
    check('Bundle loads (multi-output model)',  True)
    check('Pre-computed predictions accessible',
          len(next_preds) > 0, f"Top Category: {top_name.title()} ({top_units:,} units)")
except Exception as e:
    check('category_sales_predictor.pkl', False, str(e))

print()
print(f'{BOLD}=== Verification Complete ==={RESET}\n')
