# connections.py
from motor.motor_asyncio import AsyncIOMotorClient  
from config.config import settings  # your Pydantic Settings class

db = None
otps_collection = None
models_collection = None
users_collection = None
predictions_collection = None
jobs_collection = None
async def init_db():
    global db, users_collection, models_collection, predictions_collection, jobs_collection, otps_collection
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]

    users_collection = db["users"]
    models_collection = db["models"]
    predictions_collection = db["predictions"]
    jobs_collection = db["jobs"]
    otps_collection = db["otps"]

    # Create TTL index for OTPs
    await otps_collection.create_index("expires_at", expireAfterSeconds=0)
