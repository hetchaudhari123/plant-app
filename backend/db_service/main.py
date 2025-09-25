from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from db.connections import init_db
from routes.users_routes import router as users_router
from routes.otps_routes import router as otps_router
from routes.predictions_routes import router as predictions_router
from routes.jobs_routes import router as jobs_router

# ----------------------------
# Lifespan for startup/shutdown
# ----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ----- Startup logic -----
    await init_db()  # initialize MongoDB connection
    print("✅ MongoDB connected successfully")


    yield  # application runs here

    # ----- Shutdown logic (optional) -----
    # e.g., close DB connections if needed
    print("DB Service shutting down")


# ----------------------------
# Create FastAPI app
# ----------------------------
app = FastAPI(
    title="DB Service",
    description="Microservice responsible for database operations",
    version="1.0.0",
    lifespan=lifespan
)

# ----------------------------
# CORS middleware
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Include routers
# ----------------------------
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(otps_router, prefix="/otps", tags=["OTPs"])
app.include_router(predictions_router, prefix="/predictions", tags=["Predictions"])
app.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])


@app.get("/health")
async def health():
    return {"status": "ok"}

# ----------------------------
# Root endpoint
# ----------------------------
@app.get("/")
async def root():
    return {"message": "Welcome to DB Service 🚀"}
