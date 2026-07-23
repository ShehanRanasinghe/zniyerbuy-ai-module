"""
app/routers/trending.py
-----------------------------------
STUB — placeholder created because this router was referenced by main.py
(`from app.routers import recommendations, demand, trending, insights, predictions`)
but the actual trending.py file was not present in the uploaded ai-module
project. Without this stub, the whole FastAPI app fails to start with:
  ImportError: cannot import name 'trending' from 'app.routers'
which also takes down /predictions/shop/{shop_id} (and everything else),
since main.py imports all five routers together at module load time.

Replace this file with your real trending implementation when ready —
this stub only returns a 501 so the service boots and the rest of the
API (including the seller Analytics predictions) works correctly.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def trending_not_implemented():
    return {
        "status": "not_implemented",
        "message": "The trending router is a placeholder. Replace app/routers/trending.py with the real implementation.",
    }
