import db.connections as db_conn
from datetime import datetime
from typing import Dict, Any

async def delete_predictions_by_user(user_id: str):
    result = await db_conn.predictions_collection.delete_many({"user_id": user_id})
    return result.deleted_count



async def insert_prediction(pred_doc: Dict[str, Any]):
    """
    Insert a prediction document into the predictions collection.

    Args:
        pred_doc (dict): prediction document to insert

    Returns:
        dict: inserted document with '_id' field as string
    """
    
    result = await db_conn.predictions_collection.insert_one(pred_doc)
    pred_doc["_id"] = str(result.inserted_id)
    return pred_doc
