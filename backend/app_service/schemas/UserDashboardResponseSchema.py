from pydantic import BaseModel

class UserDashboardResponse(BaseModel):
    user_id: str
    total_analyses: int
    issues_detected: int
    crops_monitored: int
    healthy_crops: int
