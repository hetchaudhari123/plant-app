from fastapi import FastAPI
from routes.prediction_router import router as prediction_router
from routes.auth_router import router as auth_router
from routes.profile_router import router as profile_router
import config.cloudinary 

# Create FastAPI app with lifespan
app = FastAPI(title="Plant App 🌱")

# ----------------------------
# Include routers
# ----------------------------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(profile_router, prefix="/profile", tags=["Profile"])
app.include_router(prediction_router, prefix="/prediction", tags=["Prediction"])

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Welcome to Plant App 🌱 API"}
