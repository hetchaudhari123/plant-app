from typing import Any, Optional
import torch
import joblib  # for ensemble.pkl
from torchvision import models as tv_models, transforms
import torch.nn as nn
from PIL import Image
import numpy as np


class PlantModel:
    def __init__(
        self,
        name: str,
        model_path: str,
        model_type: str,
        num_classes: int = None,
        model_order: list = None,
        device="cpu",
    ):
        """
        model_type: 'pytorch' or 'sklearn'
        num_classes: required for PyTorch models to rebuild the classifier
        """
        self.name = name
        self.device = device
        self.model_type = model_type
        self.model_path = model_path
        self.num_classes = num_classes
        self.model = self.load_model()
        self.last_output = None
        self.model_order = model_order

    def load_model(self) -> Any:
        if self.model_type == "pytorch":
            model = self.build_model_arch()
            checkpoint = torch.load(self.model_path, map_location=self.device)
            state_dict = checkpoint.get("model_state", checkpoint)
            model.load_state_dict(state_dict)
            model.to(self.device)
            model.eval()
            return model
        elif self.model_type == "sklearn":
            return joblib.load(self.model_path)
        else:
            raise ValueError("Unsupported model type")

    def build_model_arch(self) -> nn.Module:
        """Rebuild the architecture with the correct number of classes"""
        if self.name.startswith("resnet"):
            model = getattr(tv_models, self.name)(weights=None)
            model.fc = nn.Linear(model.fc.in_features, self.num_classes)
        elif self.name.startswith("efficientnet"):
            model = getattr(tv_models, self.name)(weights=None)
            model.classifier[1] = nn.Linear(
                model.classifier[1].in_features, self.num_classes
            )
        elif self.name.startswith("densenet"):
            model = getattr(tv_models, self.name)(weights=None)
            model.classifier = nn.Linear(model.classifier.in_features, self.num_classes)
        elif self.name.startswith("mobilenet"):
            model = getattr(tv_models, self.name)(weights=None)
            model.classifier[3] = nn.Linear(
                model.classifier[3].in_features, self.num_classes
            )
        else:
            raise ValueError(f"Model {self.name} not supported")
        return model

    def preprocess_input(self, image: Image.Image) -> torch.Tensor:
        """Apply standard preprocessing for PyTorch base models and return a batch tensor"""
        image = image.convert("RGB")
        transform = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )
        input_tensor = transform(image).unsqueeze(0)  # Add batch dim
        return input_tensor.to(self.device)

    def _get_base_model_probs_from_manager(
        self, image: Image.Image, manager: Any
    ) -> np.ndarray:
        """
        Given a PIL image and a ModelManager, ask each non-ensemble PyTorch model for probabilities,
        then concatenate them into a single 1D feature vector (shape (1, total_features)).
        """
        if manager is None:
            raise ValueError(
                "ModelManager is required to assemble stacked features for ensemble model."
            )

        probs_list = []
        for m_name in self.model_order:
            if m_name not in manager.models:
                raise ValueError(f"Base model '{m_name}' not found in manager.")
            plant_model = manager.models[m_name]

            if plant_model.model_type != "pytorch":
                raise ValueError(f"Base model '{m_name}' must be PyTorch for stacking.")

            # Call base model predict with PIL image, manager=None to avoid recursion
            base_out = plant_model.predict(image, manager=None)

            # Ensure shape is (1, num_classes)
            base_out = np.asarray(base_out)
            if base_out.ndim == 1:
                base_out = base_out.reshape(1, -1)

            probs_list.append(base_out.flatten())

        if not probs_list:
            raise ValueError(
                "No base PyTorch models found in manager to build features for ensemble."
            )

        stacked = np.concatenate(probs_list).reshape(
            1, -1
        )  # shape (1, sum(num_classes_per_model))
        return stacked

    def predict(self, input_data: Any, manager: Optional[Any] = None) -> Any:
        """
        Predict can accept:
          - PIL.Image.Image (preferred for single-image prediction)
          - torch.Tensor (preprocessed batch tensor for pytorch)
          - numpy array / 2D features for sklearn
        For sklearn ensemble models that need base model predictions, pass `manager` so features can be assembled.
        """
        # If user passed a PIL image, handle preprocessing (or assembling stacked features)
        if isinstance(input_data, Image.Image):
            if self.model_type == "pytorch":
                # preprocess and forward
                input_tensor = self.preprocess_input(input_data)  # already on device
                with torch.no_grad():
                    out = self.model(input_tensor)  # logits
                    probs = torch.softmax(out, dim=1).cpu().numpy()  # (1, num_classes)
                self.last_output = probs
                return probs

            elif self.model_type == "sklearn":
                # For the stacking ensemble: gather base model probs via manager and then call sklearn
                stacked_features = self._get_base_model_probs_from_manager(
                    input_data, manager
                )

                prediction = self.model.predict(
                    stacked_features
                )  # class indices, shape (1,)
                probs = None

                if hasattr(self.model, "predict_proba"):
                    probs = self.model.predict_proba(
                        stacked_features
                    )  # (1, num_classes)

                # Store last output as tuple (prediction, probs)
                self.last_output = (prediction, probs)

                # Always return both, so caller can decide how to use
                return prediction, probs

            else:
                raise ValueError("Unsupported model type")

        # Fallback: unsupported input
        raise ValueError(
            "Unsupported input_data type for predict(). Pass a PIL.Image, torch.Tensor or numpy array."
        )
