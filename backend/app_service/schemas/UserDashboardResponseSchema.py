from pydantic import BaseModel
from typing import List

class UserDashboardResponse(BaseModel):
    user_id: str
    total_analyses: int
    issues_detected: int
    crops_monitored: int
