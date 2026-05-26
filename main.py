from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import recommendations, demand, trending

app = FastAPI(
    title="ZniyerBuy AI Module",
    description="AI service for product recommendations and demand prediction",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(demand.router, prefix="/demand", tags=["Demand"])
app.include_router(trending.router, prefix="/trending", tags=["Trending"])

@app.get("/")
def root():
    return {
        "service": "ZniyerBuy AI Module",
        "status": "running",
        "version": "1.0.0",
        "endpoints": [
            "/recommendations/products",
            "/demand/predict",
            "/trending/products"
        ]
    }