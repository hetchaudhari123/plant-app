# connections.py
from motor.motor_asyncio import AsyncIOMotorClient  
from config.config import settings  # your Pydantic Settings class
import asyncio

db = None
models_collection = None


async def init_db(retries = 5, delay = 2):
    global db, models_collection
    for attempt in range(retries):
        try:
            client = AsyncIOMotorClient(settings.MONGO_URI)
            # Try a simple command to check if Mongo is up
            await client.admin.command("ping")
            db = client[settings.MONGO_DB_NAME]

            models_collection = db["models"]
            # print("✅ MongoDB connected successfully")
            return

        except Exception as e:
            print(f"MongoDB not ready yet (attempt {attempt+1}/{retries}): {e}")
            await asyncio.sleep(delay)

    raise Exception("❌ Failed to connect to MongoDB after several retries")
