from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes.prediction_route import router as model_router
from dependencies import get_manager
import db.connections as db_conn


# ------------------------
# Lifespan event handler for startup/shutdown
# ------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database connection
    print("🚀 Starting up...")
    await db_conn.init_db()
    print("✅ Database initialized successfully")

    yield

    # Shutdown: Cleanup if needed
    print("🔴 Shutting down...")


# ------------------------
# FastAPI app initialization
# ------------------------
app = FastAPI(
    title="Plant Model Service",
    description="Microservice for plant disease predictions using multiple models",
    version="1.0.0",
    lifespan=lifespan,
)

# ------------------------
# CORS
# ------------------------
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# Include the routes
# ------------------------
app.include_router(model_router, prefix="/model", tags=["Model"])

# ------------------------
# Root health endpoint using dependency injection
# ------------------------


@app.get("/health")
async def health():
    """Health check endpoint"""
    db_status = "connected" if db_conn.models_collection is not None else "disconnected"
    return {"status": "ok", "database": db_status}


@app.get("/")
async def root(manager=Depends(get_manager)):
    """
    Endpoint returning status and loaded models.
    """
    db_status = "connected" if db_conn.models_collection is not None else "disconnected"
    return {
        "status": "model_service running",
        "models_loaded": list(manager.models.keys()),
        "database": db_status,
    }
