import db.connections as db_conn
from typing import Optional

async def get_user_by_email(email: str):
    return await db_conn.users_collection.find_one({"email": email})

async def create_user(user_doc: dict):
    result = await db_conn.users_collection.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)  # serialize ObjectId
    return user_doc


async def get_user_by_id(user_id: str):
    return await db_conn.users_collection.find_one({"id": user_id})


async def update_user_password(user_id: str, new_password_hash: str):
    updated_user = await db_conn.users_collection.find_one_and_update(
        {"id": user_id},
        {
            "$set": {"password_hash": new_password_hash},
            "$inc": {"token_version": 1}  # increment token_version
        },
        return_document=True  # returns the updated document
    )
    if updated_user:
        updated_user["_id"] = str(updated_user["_id"])  # serialize ObjectId
    return updated_user



# async def update_reset_token(user_id: str, token: str, expires_at: str):
async def update_reset_token(user_id: str, token: Optional[str], expires_at: Optional[str]):
    updated_user = await db_conn.users_collection.update_one(
        {"id": user_id},
        {
            "$set": {
                "reset_token": token,
                "reset_token_expires_at": expires_at
            }
        }
    )

    
    return {"matched_count": updated_user.matched_count, "modified_count": updated_user.modified_count}


async def get_user_by_reset_token(token: str):
    return await db_conn.users_collection.find_one({"reset_token": token})


async def update_user_profile(user_id: str, update_fields: dict):
    if not update_fields:
        return None

    updated_user = await db_conn.users_collection.find_one_and_update(
        {"id": user_id},
        {"$set": update_fields},
        return_document=True  # returns the updated document
    )
    if updated_user:
        updated_user["_id"] = str(updated_user["_id"])  # serialize ObjectId
    return updated_user


async def delete_user(user_id: str):
    result = await db_conn.users_collection.delete_one({"id": user_id})
    return result.deleted_count


async def update_user_profile_pic(user_id: str, new_pic_url: str):
    updated_user = await db_conn.users_collection.find_one_and_update(
        {"id": user_id},
        {"$set": {"profile_pic_url": new_pic_url}},
        return_document=True  # returns the updated document
    )
    if updated_user:
        updated_user["_id"] = str(updated_user["_id"])  # serialize ObjectId
    return updated_user