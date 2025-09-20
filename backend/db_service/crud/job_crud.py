import db.connections as db_conn

async def delete_jobs_by_user(user_id: str):
    result = await db_conn.jobs_collection.delete_many({"user_id": user_id})
    return result.deleted_count
