from motor.motor_asyncio import AsyncIOMotorClient  
from config.config import settings  
import asyncio

db = None
models_collection = None


async def init_db(retries = 5, delay = 2):
    global db, models_collection
    for attempt in range(retries):
        try:
            client = AsyncIOMotorClient(settings.MONGO_URI)
            await client.admin.command("ping")
            db = client[settings.MONGO_DB_NAME]

            models_collection = db["models"]
            
            return

        except Exception as e:
            print(f"MongoDB not ready yet (attempt {attempt+1}/{retries}): {e}")
            await asyncio.sleep(delay)

    raise Exception("❌ Failed to connect to MongoDB after several retries")



