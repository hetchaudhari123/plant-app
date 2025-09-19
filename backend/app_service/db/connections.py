# connections.py
from motor.motor_asyncio import AsyncIOMotorClient  
from config.config import settings  # your Pydantic Settings class

# Initialize MongoDB client
client = AsyncIOMotorClient(settings.MONGO_URI)

# Select the database
db = client[settings.MONGO_DB_NAME]

# Define collections
users_collection = db["users"]
models_collection = db["models"]
predictions_collection = db["predictions"]
jobs_collection = db["jobs"]
otps_collection = db["otps"]
