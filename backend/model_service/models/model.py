from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum

class ModelStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"

class ModelDeployment(BaseModel):
    endpoint_url: str
    framework: str  # e.g., "PyTorch", "TensorFlow"
    device: str     # e.g., "GPU", "CPU"

class Model(BaseModel):
    model_id: str  # MongoDB ObjectId as string
    name: str      # Human-readable name for UI
    alias: str     # Machine-friendly name
    type: str      # Model family (CNN, ResNet, EfficientNet, etc.)
    version: str   # Version tracking
    description: str  # Model description and capabilities
    accuracy: float   # Validation/test accuracy (0.0 to 1.0)
    status: ModelStatus  # active / deprecated
    deployment: ModelDeployment
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        use_enum_values = True  # Serialize enums as their values