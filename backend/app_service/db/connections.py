from motor.motor_asyncio import AsyncIOMotorClient  
from config.config import settings  
import asyncio

db = None
otps_collection = None
users_collection = None
predictions_collection = None
otp_tokens_collection = None

async def init_db(retries = 5, delay = 2):
    global db, users_collection, predictions_collection, otps_collection, otp_tokens_collection
    for attempt in range(retries):
        try:
            client = AsyncIOMotorClient(settings.MONGO_URI)
            # Try a simple command to check if Mongo is up
            await client.admin.command("ping")
            db = client[settings.MONGO_DB_NAME]

            users_collection = db["users"]
            predictions_collection = db["predictions"]
            otps_collection = db["otps"]
            otp_tokens_collection = db["otptokens"]

            # Create TTL indexes
            await otps_collection.create_index("expires_at", expireAfterSeconds=0)
            await predictions_collection.create_index("expires_at", expireAfterSeconds=0)
            await otp_tokens_collection.create_index("expires_at", expireAfterSeconds=0)

            return

        except Exception as e:
            print(f"MongoDB not ready yet (attempt {attempt+1}/{retries}): {e}")
            await asyncio.sleep(delay)

    raise Exception("❌ Failed to connect to MongoDB after several retries")
