from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import recommendations, demand, trending, insights, predictions
from app.database import health_check
import time
import os

app = FastAPI(
    title="ZniyerBuy AI Module",
    description="AI service for product recommendations, demand prediction, trending analysis, and admin insights",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# CORS Configuration
# In production, replace ["*"] with specific allowed origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only allow necessary methods
    allow_headers=["Content-Type", "Authorization"],  # Only allow necessary headers
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests for monitoring and debugging.
    """
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log request details
    print(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    # Add processing time to response headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    print(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An error occurred"
        }
    )

# Include routers
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(demand.router, prefix="/demand", tags=["Demand Prediction"])
app.include_router(trending.router, prefix="/trending", tags=["Trending Analysis"])
app.include_router(insights.router, prefix="/insights", tags=["Admin Insights"])
app.include_router(predictions.router, prefix="/predictions", tags=["AI Predictions"])

@app.get("/", tags=["Health"])
def root():
    """
    Root endpoint - returns service information and available endpoints.
    """
    return {
        "service": "ZniyerBuy AI Module",
        "status": "running",
        "version": "1.0.0",
        "description": "AI-powered recommendations, demand prediction, and analytics",
        "endpoints": {
            "recommendations": "/recommendations/products",
            "demand_prediction": "/demand/predict",
            "trending_products": "/trending/products",
            "trending_categories": "/trending/categories",
            "admin_insights": "/insights/generate",
            "shop_predictions": "/predictions/shop/{shop_id}",
            "health_check": "/health",
            "documentation": "/docs"
        }
    }

@app.get("/health", tags=["Health"])
def health():
    """
    Health check endpoint - verifies service and database connectivity.
    """
    db_health = health_check()
    
    return {
        "service": "ZniyerBuy AI Module",
        "status": "healthy" if db_health["status"] == "connected" else "degraded",
        "version": "1.0.0",
        "database": db_health,
        "timestamp": time.time()
    }

@app.get("/version", tags=["Health"])
def version():
    """
    Version endpoint - returns current version and build info.
    """
    return {
        "version": "1.0.0",
        "service": "ZniyerBuy AI Module",
        "python_version": "3.8+",
        "framework": "FastAPI"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts.
    Performs initial health checks and setup.
    """
    print("=" * 50)
    print("ZniyerBuy AI Module Starting")
    print("=" * 50)
    
    # Check database connection
    db_health = health_check()
    if db_health["status"] == "connected":
        print("Database Connected Successfully.")
    else:
        print(f"Database connection: FAILED - {db_health.get('error', 'Unknown error')}")
    
    print("=" * 50)
    print("AI Module Ready!")
    print("Documentation: http://localhost:8000/docs")
    print("=" * 50)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs when the application shuts down.
    Performs cleanup operations.
    """
    print("=" * 50)
    print("ZniyerBuy AI Module Shutting Down.")
    print("=" * 50)