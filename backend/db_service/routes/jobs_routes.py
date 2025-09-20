from fastapi import APIRouter

from crud.job_crud import delete_jobs_by_user  # import your function

router = APIRouter()

@router.delete("/user/{user_id}")
async def delete_jobs_for_user_endpoint(user_id: str):
    deleted_count = await delete_jobs_by_user(user_id)
    if deleted_count == 0:
        return {"deleted_count": 0, "message": "No jobs found for this user"}
    return {"deleted_count": deleted_count, "message": f"Deleted {deleted_count} jobs for user"}
