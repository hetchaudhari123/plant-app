from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.connections import users_collection, otps_collection
from routes import auth_router, profile_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ----- Startup logic -----
    await otps_collection.create_index("expires_at", expireAfterSeconds=0)
    print("✅ TTL indexes ensured for OTP and reset token collections")

    yield  # application runs here

    # ----- Shutdown logic (optional) -----
    # e.g., close DB connections if needed

# Create FastAPI app with lifespan
app = FastAPI(title="Plant App 🌱", lifespan=lifespan)

# ----------------------------
# Include routers
# ----------------------------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(profile_router, prefix="/profile", tags=["Profile"])

@app.get("/")
def root():
    return {"message": "Welcome to Plant App 🌱 API"}
