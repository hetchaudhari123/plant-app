from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from routes.prediction_route import router as model_router
from dependencies import get_manager  # get_idx2label not needed for health

# ------------------------
# FastAPI app initialization
# ------------------------
app = FastAPI(
    title="Plant Model Service",
    description="Microservice for plant disease predictions using multiple models",
    version="1.0.0"
)

# ------------------------
# CORS (optional)
# ------------------------
origins = ["*"]  # adjust to your frontend domain(s) for security
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
app.include_router(model_router, prefix="/models", tags=["Model"])

# ------------------------
# Root health endpoint using dependency injection
# ------------------------
@app.get("/", tags=["Health"])
async def root(manager=Depends(get_manager)):
    """
    Health check endpoint returning status and loaded models.
    """
    return {
        "status": "model_service running",
        "models_loaded": list(manager.models.keys())
    }
