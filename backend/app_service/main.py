from fastapi import FastAPI
from routes import auth_router, profile_router, prediction_router
import config.cloudinary

# Create FastAPI app with lifespan
app = FastAPI(title="Plant App 🌱")

# ----------------------------
# Include routers
# ----------------------------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(profile_router, prefix="/profile", tags=["Profile"])
app.include_router(prediction_router, prefix="/prediction", tags=["Prediction"])

@app.get("/")
def root():
    return {"message": "Welcome to Plant App 🌱 API"}
