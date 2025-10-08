from typing import Any
from .plant_model import PlantModel


class ModelManager:
    def __init__(self):
        self.models = {}

    def register_model(self, model: PlantModel):
        self.models[model.name] = model

    def predict(self, model_name: str, input_data: Any):
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        model = self.models[model_name]

        # For ensemble models, pass the manager so base model predictions can be collected
        if (
            model.model_type == "sklearn"
            and hasattr(model, "model_order")
            and model.model_order
        ):
            return model.predict(input_data, manager=self)
        else:
            # For PyTorch models or sklearn without stacking, manager is not needed
            return model.predict(input_data)
