import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import UploadFile
from PIL import Image
import io
import numpy as np
from fastapi import HTTPException
from services.prediction_service import (
    predict_service,
    get_all_models_service,
    get_active_models_service,
    get_model_by_alias_service,
    get_model_by_id_service,
)
import asyncio
from bson import ObjectId


@pytest.mark.asyncio
async def test_predict_ensemble_model_success():
    """Test successful prediction with ensemble model"""
    model_name = "ensemble"

    # Create mock image file
    img = Image.new("RGB", (224, 224), color="red")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = img_byte_arr

    # Mock manager
    mock_manager = MagicMock()
    prediction = np.array([0])
    probs = np.array([[0.8, 0.15, 0.05]])
    mock_manager.predict.return_value = (prediction, probs)

    # Mock idx2label
    mock_idx2label = {"0": "healthy", "1": "diseased", "2": "pest"}

    result = await predict_service(model_name, mock_file, mock_manager, mock_idx2label)

    assert result["model"] == "ensemble"
    assert result["prediction"] == "healthy"
    assert result["confidence"] == 0.8
    assert result["raw_output"] == [0.8, 0.15, 0.05]
    mock_manager.predict.assert_called_once()


@pytest.mark.asyncio
async def test_predict_non_ensemble_model_success():
    """Test successful prediction with non-ensemble model"""
    model_name = "resnet50"

    # Create mock image file
    img = Image.new("RGB", (224, 224), color="blue")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = img_byte_arr

    # Mock manager
    mock_manager = MagicMock()
    probs = np.array([[0.1, 0.7, 0.2]])
    mock_manager.predict.return_value = probs

    # Mock idx2label
    mock_idx2label = {"0": "healthy", "1": "diseased", "2": "pest"}

    result = await predict_service(model_name, mock_file, mock_manager, mock_idx2label)

    assert result["model"] == "resnet50"
    assert result["prediction"] == "diseased"
    assert result["confidence"] == 0.7
    assert result["raw_output"] == [0.1, 0.7, 0.2]
    mock_manager.predict.assert_called_once()


@pytest.mark.asyncio
async def test_predict_multiple_models():
    """Test prediction with different model names"""
    model_names = ["resnet50", "vgg16", "mobilenet", "efficientnet"]

    for model_name in model_names:
        img = Image.new("RGB", (224, 224), color="green")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_byte_arr.seek(0)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.file = img_byte_arr

        mock_manager = MagicMock()
        probs = np.array([[0.3, 0.5, 0.2]])
        mock_manager.predict.return_value = probs

        mock_idx2label = {"0": "class_0", "1": "class_1", "2": "class_2"}

        result = await predict_service(
            model_name, mock_file, mock_manager, mock_idx2label
        )

        assert result["model"] == model_name
        assert result["prediction"] == "class_1"
        assert result["confidence"] == 0.5


@pytest.mark.asyncio
async def test_predict_ensemble_with_none_probs():
    """Test ensemble model when probs is None"""
    model_name = "ensemble"

    img = Image.new("RGB", (224, 224), color="yellow")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = img_byte_arr

    mock_manager = MagicMock()
    prediction = np.array([2])
    mock_manager.predict.return_value = (prediction, None)

    mock_idx2label = {"0": "healthy", "1": "diseased", "2": "pest"}

    result = await predict_service(model_name, mock_file, mock_manager, mock_idx2label)

    assert result["model"] == "ensemble"
    assert result["prediction"] == "pest"
    assert result["confidence"] is None
    assert result["raw_output"] is None


@pytest.mark.asyncio
async def test_predict_different_class_counts():
    """Test prediction with different numbers of classes"""
    class_counts = [2, 3, 5, 10]

    for num_classes in class_counts:
        img = Image.new("RGB", (224, 224), color="purple")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_byte_arr.seek(0)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.file = img_byte_arr

        mock_manager = MagicMock()
        probs = np.random.dirichlet(np.ones(num_classes), size=1)
        mock_manager.predict.return_value = probs

        mock_idx2label = {str(i): f"class_{i}" for i in range(num_classes)}

        result = await predict_service(
            "test_model", mock_file, mock_manager, mock_idx2label
        )

        assert len(result["raw_output"]) == num_classes
        assert result["confidence"] > 0 and result["confidence"] <= 1


@pytest.mark.asyncio
async def test_predict_invalid_image():
    """Test prediction with invalid image file"""
    model_name = "resnet50"

    # Create invalid image file
    invalid_data = io.BytesIO(b"not an image")

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = invalid_data

    mock_manager = MagicMock()
    mock_idx2label = {"0": "healthy", "1": "diseased"}

    with pytest.raises(HTTPException) as exc_info:
        await predict_service(model_name, mock_file, mock_manager, mock_idx2label)

    assert exc_info.value.status_code == 500
    assert "Prediction failed" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_predict_manager_prediction_fails():
    """Test when manager.predict raises an exception"""
    model_name = "resnet50"

    img = Image.new("RGB", (224, 224), color="cyan")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = img_byte_arr

    mock_manager = MagicMock()
    mock_manager.predict.side_effect = Exception("Model prediction error")

    mock_idx2label = {"0": "healthy", "1": "diseased"}

    with pytest.raises(HTTPException) as exc_info:
        await predict_service(model_name, mock_file, mock_manager, mock_idx2label)

    assert exc_info.value.status_code == 500
    assert "Prediction failed" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_predict_grayscale_image_conversion():
    """Test prediction with grayscale image (should be converted to RGB)"""
    model_name = "resnet50"

    # Create grayscale image
    img = Image.new("L", (224, 224), color=128)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = img_byte_arr

    mock_manager = MagicMock()
    probs = np.array([[0.6, 0.4]])
    mock_manager.predict.return_value = probs

    mock_idx2label = {"0": "healthy", "1": "diseased"}

    result = await predict_service(model_name, mock_file, mock_manager, mock_idx2label)

    assert result["prediction"] == "healthy"
    # Verify that predict was called (image was successfully converted)
    mock_manager.predict.assert_called_once()


@pytest.mark.asyncio
async def test_predict_high_confidence():
    """Test prediction with very high confidence"""
    model_name = "resnet50"

    img = Image.new("RGB", (224, 224), color="orange")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = img_byte_arr

    mock_manager = MagicMock()
    probs = np.array([[0.99, 0.005, 0.005]])
    mock_manager.predict.return_value = probs

    mock_idx2label = {"0": "healthy", "1": "diseased", "2": "pest"}

    result = await predict_service(model_name, mock_file, mock_manager, mock_idx2label)

    assert result["confidence"] == 0.99
    assert result["prediction"] == "healthy"


@pytest.mark.asyncio
async def test_predict_low_confidence():
    """Test prediction with low confidence (nearly uniform distribution)"""
    model_name = "resnet50"

    img = Image.new("RGB", (224, 224), color="brown")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = img_byte_arr

    mock_manager = MagicMock()
    probs = np.array([[0.34, 0.33, 0.33]])
    mock_manager.predict.return_value = probs

    mock_idx2label = {"0": "healthy", "1": "diseased", "2": "pest"}

    result = await predict_service(model_name, mock_file, mock_manager, mock_idx2label)

    assert result["confidence"] == 0.34
    assert result["prediction"] == "healthy"


@pytest.mark.asyncio
async def test_predict_ensemble_different_predictions():
    """Test ensemble model with different predicted indices"""
    model_name = "ensemble"
    predicted_indices = [0, 1, 2, 3]

    for pred_idx in predicted_indices:
        img = Image.new("RGB", (224, 224), color="pink")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_byte_arr.seek(0)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.file = img_byte_arr

        mock_manager = MagicMock()
        prediction = np.array([pred_idx])
        probs = np.zeros((1, 4))
        probs[0, pred_idx] = 0.9
        probs[0, (pred_idx + 1) % 4] = 0.1
        mock_manager.predict.return_value = (prediction, probs)

        mock_idx2label = {
            "0": "class_0",
            "1": "class_1",
            "2": "class_2",
            "3": "class_3",
        }

        result = await predict_service(
            model_name, mock_file, mock_manager, mock_idx2label
        )

        assert result["prediction"] == f"class_{pred_idx}"
        assert result["confidence"] == 0.9


@pytest.mark.asyncio
async def test_predict_missing_idx2label_key():
    """Test prediction when idx2label doesn't have the predicted index"""
    model_name = "resnet50"

    img = Image.new("RGB", (224, 224), color="gray")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = img_byte_arr

    mock_manager = MagicMock()
    probs = np.array([[0.2, 0.3, 0.5]])
    mock_manager.predict.return_value = probs

    # idx2label missing key "2"
    mock_idx2label = {"0": "healthy", "1": "diseased"}

    with pytest.raises(HTTPException) as exc_info:
        await predict_service(model_name, mock_file, mock_manager, mock_idx2label)

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_get_all_models_no_filters():
    """Test fetching all models without any filters"""
    mock_models = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "model_id": ObjectId("507f1f77bcf86cd799439012"),
            "name": "resnet50",
            "type": "ResNet",
            "status": "active",
            "accuracy": 0.95,
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "model_id": ObjectId("507f1f77bcf86cd799439014"),
            "name": "vgg16",
            "type": "VGG",
            "status": "active",
            "accuracy": 0.92,
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_models.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_all_models_service()

        assert len(result) == 2
        assert result[0]["name"] == "resnet50"
        assert result[1]["name"] == "vgg16"
        # Check ObjectId conversion to string
        assert isinstance(result[0]["_id"], str)
        assert isinstance(result[0]["model_id"], str)

        mock_db_conn.models_collection.find.assert_called_once_with({})
        mock_cursor.to_list.assert_awaited_once_with(length=None)


@pytest.mark.asyncio
async def test_get_all_models_filter_by_status():
    """Test fetching models filtered by status"""
    statuses = ["active", "deprecated", "testing"]

    for status in statuses:
        mock_models = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "model_id": ObjectId("507f1f77bcf86cd799439012"),
                "name": "model1",
                "type": "ResNet",
                "status": status,
                "accuracy": 0.90,
            }
        ]

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_models.copy())

        mock_db_conn = MagicMock()
        mock_db_conn.models_collection = MagicMock()
        mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

        with patch("services.prediction_service.db_conn", mock_db_conn):
            result = await get_all_models_service(status=status)

            assert len(result) == 1
            assert result[0]["status"] == status

            mock_db_conn.models_collection.find.assert_called_once_with(
                {"status": status}
            )


@pytest.mark.asyncio
async def test_get_all_models_filter_by_model_type():
    """Test fetching models filtered by model type"""
    model_types = ["CNN", "ResNet", "VGG", "EfficientNet", "MobileNet"]

    for model_type in model_types:
        mock_models = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "model_id": ObjectId("507f1f77bcf86cd799439012"),
                "name": f"{model_type.lower()}_model",
                "type": model_type,
                "status": "active",
                "accuracy": 0.88,
            }
        ]

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_models.copy())

        mock_db_conn = MagicMock()
        mock_db_conn.models_collection = MagicMock()
        mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

        with patch("services.prediction_service.db_conn", mock_db_conn):
            result = await get_all_models_service(model_type=model_type)

            assert len(result) == 1
            assert result[0]["type"] == model_type

            mock_db_conn.models_collection.find.assert_called_once_with(
                {"type": model_type}
            )


@pytest.mark.asyncio
async def test_get_all_models_filter_by_status_and_type():
    """Test fetching models with both status and type filters"""
    mock_models = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "model_id": ObjectId("507f1f77bcf86cd799439012"),
            "name": "resnet50",
            "type": "ResNet",
            "status": "active",
            "accuracy": 0.95,
        }
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_models.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_all_models_service(status="active", model_type="ResNet")

        assert len(result) == 1
        assert result[0]["status"] == "active"
        assert result[0]["type"] == "ResNet"

        mock_db_conn.models_collection.find.assert_called_once_with(
            {"status": "active", "type": "ResNet"}
        )


@pytest.mark.asyncio
async def test_get_all_models_empty_result():
    """Test fetching models when no models match the filter"""
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_all_models_service(status="nonexistent")

        assert len(result) == 0
        assert result == []


@pytest.mark.asyncio
async def test_get_all_models_large_dataset():
    """Test fetching a large number of models"""
    mock_models = [
        {
            "_id": ObjectId(),
            "model_id": ObjectId(),
            "name": f"model_{i}",
            "type": "CNN",
            "status": "active",
            "accuracy": 0.80 + (i * 0.01),
        }
        for i in range(100)
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_models.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_all_models_service()

        assert len(result) == 100
        # Verify all ObjectIds were converted to strings
        for model in result:
            assert isinstance(model["_id"], str)
            assert isinstance(model["model_id"], str)


@pytest.mark.asyncio
async def test_get_all_models_without_model_id_field():
    """Test fetching models that don't have model_id field"""
    mock_models = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "name": "legacy_model",
            "type": "CNN",
            "status": "deprecated",
            "accuracy": 0.75,
        }
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_models.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_all_models_service()

        assert len(result) == 1
        assert isinstance(result[0]["_id"], str)
        assert "model_id" not in result[0]


@pytest.mark.asyncio
async def test_get_all_models_database_error():
    """Test handling of database errors"""
    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find.side_effect = Exception(
        "Database connection failed"
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_all_models_service()

        assert exc_info.value.status_code == 500
        assert "Failed to fetch models" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_all_models_cursor_error():
    """Test handling of cursor.to_list errors"""
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(side_effect=Exception("Cursor conversion failed"))

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_all_models_service()

        assert exc_info.value.status_code == 500
        assert "Failed to fetch models" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_all_models_mixed_fields():
    """Test models with various optional fields present/absent"""
    mock_models = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "model_id": ObjectId("507f1f77bcf86cd799439012"),
            "name": "model1",
            "type": "CNN",
            "status": "active",
            "accuracy": 0.95,
            "created_at": "2024-01-01",
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "name": "model2",
            "type": "ResNet",
            "status": "active",
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439014"),
            "model_id": ObjectId("507f1f77bcf86cd799439015"),
            "name": "model3",
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_models.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_all_models_service()

        assert len(result) == 3
        # Check first model has all fields converted
        assert isinstance(result[0]["_id"], str)
        assert isinstance(result[0]["model_id"], str)
        # Check second model missing model_id
        assert isinstance(result[1]["_id"], str)
        assert "model_id" not in result[1]
        # Check third model has both IDs
        assert isinstance(result[2]["_id"], str)
        assert isinstance(result[2]["model_id"], str)


@pytest.mark.asyncio
async def test_get_all_models_none_filters():
    """Test explicitly passing None for filters"""
    mock_models = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "model_id": ObjectId("507f1f77bcf86cd799439012"),
            "name": "test_model",
            "type": "CNN",
            "status": "active",
        }
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_models.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_all_models_service(status=None, model_type=None)

        assert len(result) == 1
        # Verify empty query when both filters are None
        mock_db_conn.models_collection.find.assert_called_once_with({})


@pytest.mark.asyncio
async def test_get_all_models_objectid_conversion():
    """Test that ObjectId fields are properly converted to strings"""
    original_id = ObjectId("507f1f77bcf86cd799439011")
    original_model_id = ObjectId("507f1f77bcf86cd799439012")

    mock_models = [
        {
            "_id": original_id,
            "model_id": original_model_id,
            "name": "test_model",
            "type": "CNN",
            "status": "active",
        }
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_models.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_all_models_service()

        assert result[0]["_id"] == str(original_id)
        assert result[0]["model_id"] == str(original_model_id)
        assert result[0]["_id"] == "507f1f77bcf86cd799439011"
        assert result[0]["model_id"] == "507f1f77bcf86cd799439012"


@pytest.mark.asyncio
async def test_get_all_models_special_characters_in_filters():
    """Test filters with special characters"""
    mock_models = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "model_id": ObjectId("507f1f77bcf86cd799439012"),
            "name": "model_v2.1",
            "type": "ResNet-50",
            "status": "active-prod",
        }
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_models.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_all_models_service(
            status="active-prod", model_type="ResNet-50"
        )

        assert len(result) == 1
        assert result[0]["status"] == "active-prod"
        assert result[0]["type"] == "ResNet-50"


@pytest.mark.asyncio
async def test_get_all_models_endpoint_response_format():
    """Test the endpoint returns proper response format with count"""
    mock_models = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "model_id": ObjectId("507f1f77bcf86cd799439012"),
            "name": "model1",
            "type": "CNN",
            "status": "active",
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "model_id": ObjectId("507f1f77bcf86cd799439014"),
            "name": "model2",
            "type": "ResNet",
            "status": "active",
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_models.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        models = await get_all_models_service()
        response = {"models": models, "count": len(models)}

        assert "models" in response
        assert "count" in response
        assert response["count"] == 2
        assert len(response["models"]) == 2


@pytest.mark.asyncio
async def test_get_active_models_success():
    """Test fetching active models successfully"""
    mock_models = [
        {
            "_id": "507f1f77bcf86cd799439011",
            "model_id": "507f1f77bcf86cd799439012",
            "name": "resnet50",
            "type": "ResNet",
            "status": "active",
            "accuracy": 0.95,
        },
        {
            "_id": "507f1f77bcf86cd799439013",
            "model_id": "507f1f77bcf86cd799439014",
            "name": "vgg16",
            "type": "VGG",
            "status": "active",
            "accuracy": 0.92,
        },
    ]

    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = mock_models

        result = await get_active_models_service()

        assert len(result) == 2
        assert result[0]["status"] == "active"
        assert result[1]["status"] == "active"
        assert result[0]["name"] == "resnet50"
        assert result[1]["name"] == "vgg16"

        mock_get_all.assert_awaited_once_with(status="active")


@pytest.mark.asyncio
async def test_get_active_models_empty_result():
    """Test fetching active models when none exist"""
    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = []

        result = await get_active_models_service()

        assert len(result) == 0
        assert result == []

        mock_get_all.assert_awaited_once_with(status="active")


@pytest.mark.asyncio
async def test_get_active_models_single_model():
    """Test fetching active models with only one active model"""
    mock_models = [
        {
            "_id": "507f1f77bcf86cd799439011",
            "model_id": "507f1f77bcf86cd799439012",
            "name": "efficientnet",
            "type": "EfficientNet",
            "status": "active",
            "accuracy": 0.97,
        }
    ]

    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = mock_models

        result = await get_active_models_service()

        assert len(result) == 1
        assert result[0]["name"] == "efficientnet"
        assert result[0]["status"] == "active"

        mock_get_all.assert_awaited_once_with(status="active")


@pytest.mark.asyncio
async def test_get_active_models_multiple_types():
    """Test fetching active models of different types"""
    mock_models = [
        {
            "_id": "507f1f77bcf86cd799439011",
            "model_id": "507f1f77bcf86cd799439012",
            "name": "resnet50",
            "type": "ResNet",
            "status": "active",
            "accuracy": 0.95,
        },
        {
            "_id": "507f1f77bcf86cd799439013",
            "model_id": "507f1f77bcf86cd799439014",
            "name": "vgg16",
            "type": "VGG",
            "status": "active",
            "accuracy": 0.92,
        },
        {
            "_id": "507f1f77bcf86cd799439015",
            "model_id": "507f1f77bcf86cd799439016",
            "name": "mobilenet",
            "type": "MobileNet",
            "status": "active",
            "accuracy": 0.89,
        },
    ]

    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = mock_models

        result = await get_active_models_service()

        assert len(result) == 3
        model_types = [model["type"] for model in result]
        assert "ResNet" in model_types
        assert "VGG" in model_types
        assert "MobileNet" in model_types

        # Verify all are active
        for model in result:
            assert model["status"] == "active"


@pytest.mark.asyncio
async def test_get_active_models_large_dataset():
    """Test fetching a large number of active models"""
    mock_models = [
        {
            "_id": f"507f1f77bcf86cd79943{str(i).zfill(4)}",
            "model_id": f"507f1f77bcf86cd79944{str(i).zfill(4)}",
            "name": f"model_{i}",
            "type": "CNN",
            "status": "active",
            "accuracy": 0.80 + (i * 0.001),
        }
        for i in range(50)
    ]

    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = mock_models

        result = await get_active_models_service()

        assert len(result) == 50
        # Verify all models are active
        for model in result:
            assert model["status"] == "active"

        mock_get_all.assert_awaited_once_with(status="active")


@pytest.mark.asyncio
async def test_get_active_models_with_various_accuracies():
    """Test active models with different accuracy values"""
    mock_models = [
        {
            "_id": "507f1f77bcf86cd799439011",
            "model_id": "507f1f77bcf86cd799439012",
            "name": "high_accuracy_model",
            "type": "ResNet",
            "status": "active",
            "accuracy": 0.99,
        },
        {
            "_id": "507f1f77bcf86cd799439013",
            "model_id": "507f1f77bcf86cd799439014",
            "name": "medium_accuracy_model",
            "type": "VGG",
            "status": "active",
            "accuracy": 0.85,
        },
        {
            "_id": "507f1f77bcf86cd799439015",
            "model_id": "507f1f77bcf86cd799439016",
            "name": "low_accuracy_model",
            "type": "CNN",
            "status": "active",
            "accuracy": 0.70,
        },
    ]

    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = mock_models

        result = await get_active_models_service()

        assert len(result) == 3
        accuracies = [model["accuracy"] for model in result]
        assert 0.99 in accuracies
        assert 0.85 in accuracies
        assert 0.70 in accuracies


@pytest.mark.asyncio
async def test_get_active_models_with_optional_fields():
    """Test active models with various optional fields"""
    mock_models = [
        {
            "_id": "507f1f77bcf86cd799439011",
            "model_id": "507f1f77bcf86cd799439012",
            "name": "model_with_all_fields",
            "type": "ResNet",
            "status": "active",
            "accuracy": 0.95,
            "created_at": "2024-01-01",
            "version": "1.0",
        },
        {
            "_id": "507f1f77bcf86cd799439013",
            "name": "model_minimal_fields",
            "status": "active",
        },
        {
            "_id": "507f1f77bcf86cd799439014",
            "model_id": "507f1f77bcf86cd799439015",
            "name": "model_partial_fields",
            "type": "VGG",
            "status": "active",
            "accuracy": 0.88,
        },
    ]

    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = mock_models

        result = await get_active_models_service()

        assert len(result) == 3
        # Verify first model has all fields
        assert "created_at" in result[0]
        assert "version" in result[0]
        # Verify second model has minimal fields
        assert "type" not in result[1]
        assert "accuracy" not in result[1]
        # Verify all are active
        for model in result:
            assert model["status"] == "active"


@pytest.mark.asyncio
async def test_get_active_models_service_exception():
    """Test handling when get_all_models_service raises an exception"""
    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            await get_active_models_service()

        assert "Database error" in str(exc_info.value)
        mock_get_all.assert_awaited_once_with(status="active")


@pytest.mark.asyncio
async def test_get_active_models_endpoint_response_format():
    """Test the endpoint returns proper response format with count"""
    mock_models = [
        {
            "_id": "507f1f77bcf86cd799439011",
            "model_id": "507f1f77bcf86cd799439012",
            "name": "model1",
            "type": "CNN",
            "status": "active",
        },
        {
            "_id": "507f1f77bcf86cd799439013",
            "model_id": "507f1f77bcf86cd799439014",
            "name": "model2",
            "type": "ResNet",
            "status": "active",
        },
        {
            "_id": "507f1f77bcf86cd799439015",
            "model_id": "507f1f77bcf86cd799439016",
            "name": "model3",
            "type": "VGG",
            "status": "active",
        },
    ]

    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = mock_models

        models = await get_active_models_service()
        response = {"models": models, "count": len(models)}

        assert "models" in response
        assert "count" in response
        assert response["count"] == 3
        assert len(response["models"]) == 3
        assert isinstance(response["models"], list)


@pytest.mark.asyncio
async def test_get_active_models_calls_correct_function():
    """Test that get_active_models_service calls get_all_models_service with correct parameter"""
    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = []

        await get_active_models_service()

        # Verify it was called exactly once with status="active"
        mock_get_all.assert_awaited_once()
        call_args = mock_get_all.call_args
        assert call_args.kwargs.get("status") == "active"
        # Verify model_type is not passed
        assert "model_type" not in call_args.kwargs


@pytest.mark.asyncio
async def test_get_active_models_return_type():
    """Test that get_active_models_service returns a list"""
    mock_models = [
        {"_id": "507f1f77bcf86cd799439011", "name": "test_model", "status": "active"}
    ]

    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = mock_models

        result = await get_active_models_service()

        assert isinstance(result, list)
        assert all(isinstance(model, dict) for model in result)


@pytest.mark.asyncio
async def test_get_active_models_preserves_data():
    """Test that data from get_all_models_service is preserved"""
    mock_models = [
        {
            "_id": "507f1f77bcf86cd799439011",
            "model_id": "507f1f77bcf86cd799439012",
            "name": "test_model",
            "type": "ResNet",
            "status": "active",
            "accuracy": 0.95,
            "custom_field": "custom_value",
            "metadata": {"training_date": "2024-01-01", "dataset": "imagenet"},
        }
    ]

    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = mock_models

        result = await get_active_models_service()

        # Verify all fields are preserved
        assert result[0]["_id"] == "507f1f77bcf86cd799439011"
        assert result[0]["model_id"] == "507f1f77bcf86cd799439012"
        assert result[0]["name"] == "test_model"
        assert result[0]["type"] == "ResNet"
        assert result[0]["status"] == "active"
        assert result[0]["accuracy"] == 0.95
        assert result[0]["custom_field"] == "custom_value"
        assert result[0]["metadata"]["training_date"] == "2024-01-01"
        assert result[0]["metadata"]["dataset"] == "imagenet"


@pytest.mark.asyncio
async def test_get_active_models_different_model_names():
    """Test active models with various naming conventions"""
    mock_models = [
        {"_id": "507f1f77bcf86cd799439011", "name": "resnet_50_v2", "status": "active"},
        {"_id": "507f1f77bcf86cd799439012", "name": "VGG-16", "status": "active"},
        {
            "_id": "507f1f77bcf86cd799439013",
            "name": "efficientnet.b0",
            "status": "active",
        },
        {
            "_id": "507f1f77bcf86cd799439014",
            "name": "mobilenet v3 large",
            "status": "active",
        },
    ]

    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = mock_models

        result = await get_active_models_service()

        assert len(result) == 4
        names = [model["name"] for model in result]
        assert "resnet_50_v2" in names
        assert "VGG-16" in names
        assert "efficientnet.b0" in names
        assert "mobilenet v3 large" in names


@pytest.mark.asyncio
async def test_get_active_models_concurrent_calls():
    """Test multiple concurrent calls to get_active_models_service"""
    mock_models = [
        {"_id": "507f1f77bcf86cd799439011", "name": "model1", "status": "active"}
    ]

    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = mock_models

        # Simulate concurrent calls
        results = await asyncio.gather(
            get_active_models_service(),
            get_active_models_service(),
            get_active_models_service(),
        )

        # Verify all calls succeeded
        assert len(results) == 3
        for result in results:
            assert len(result) == 1
            assert result[0]["status"] == "active"

        # Verify get_all_models_service was called 3 times
        assert mock_get_all.await_count == 3


@pytest.mark.asyncio
async def test_get_active_models_zero_count_response():
    """Test endpoint response when no active models exist"""
    with patch(
        "services.prediction_service.get_all_models_service", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = []

        models = await get_active_models_service()
        response = {"models": models, "count": len(models)}

        assert response["count"] == 0
        assert response["models"] == []
        assert isinstance(response["models"], list)


@pytest.mark.asyncio
async def test_get_model_by_alias_success():
    """Test successfully fetching a model by alias"""
    alias = "densenet121"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId("507f1f77bcf86cd799439012"),
        "alias": "densenet121",
        "name": "DenseNet-121",
        "type": "DenseNet",
        "status": "active",
        "accuracy": 0.94,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_alias_service(alias)

        assert result["alias"] == "densenet121"
        assert result["name"] == "DenseNet-121"
        assert result["type"] == "DenseNet"
        assert result["status"] == "active"
        assert isinstance(result["_id"], str)
        assert isinstance(result["model_id"], str)

        mock_db_conn.models_collection.find_one.assert_awaited_once_with(
            {"alias": alias}
        )


@pytest.mark.asyncio
async def test_get_model_by_alias_not_found():
    """Test fetching a model with non-existent alias"""
    alias = "nonexistent_model"

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_alias_service(alias)

        assert exc_info.value.status_code == 404
        assert f"Model with alias '{alias}' not found" in str(exc_info.value.detail)

        mock_db_conn.models_collection.find_one.assert_awaited_once_with(
            {"alias": alias}
        )


@pytest.mark.asyncio
async def test_get_model_by_alias_multiple_aliases():
    """Test fetching different models by various aliases"""
    aliases = ["resnet50", "vgg16", "mobilenet_v2", "efficientnet_b0"]

    for alias in aliases:
        mock_model = {
            "_id": ObjectId(),
            "model_id": ObjectId(),
            "alias": alias,
            "name": alias.upper(),
            "type": "CNN",
            "status": "active",
        }

        mock_db_conn = MagicMock()
        mock_db_conn.models_collection = MagicMock()
        mock_db_conn.models_collection.find_one = AsyncMock(
            return_value=mock_model.copy()
        )

        with patch("services.prediction_service.db_conn", mock_db_conn):
            result = await get_model_by_alias_service(alias)

            assert result["alias"] == alias
            assert isinstance(result["_id"], str)
            assert isinstance(result["model_id"], str)


@pytest.mark.asyncio
async def test_get_model_by_alias_without_model_id():
    """Test fetching a model that doesn't have model_id field"""
    alias = "legacy_model"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "alias": "legacy_model",
        "name": "Legacy Model",
        "type": "CNN",
        "status": "deprecated",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_alias_service(alias)

        assert result["alias"] == "legacy_model"
        assert isinstance(result["_id"], str)
        assert "model_id" not in result


@pytest.mark.asyncio
async def test_get_model_by_alias_objectid_conversion():
    """Test that ObjectId fields are properly converted to strings"""
    alias = "test_model"
    original_id = ObjectId("507f1f77bcf86cd799439011")
    original_model_id = ObjectId("507f1f77bcf86cd799439012")

    mock_model = {
        "_id": original_id,
        "model_id": original_model_id,
        "alias": "test_model",
        "name": "Test Model",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_alias_service(alias)

        assert result["_id"] == str(original_id)
        assert result["model_id"] == str(original_model_id)
        assert result["_id"] == "507f1f77bcf86cd799439011"
        assert result["model_id"] == "507f1f77bcf86cd799439012"


@pytest.mark.asyncio
async def test_get_model_by_alias_with_all_fields():
    """Test fetching a model with all possible fields"""
    alias = "complete_model"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId("507f1f77bcf86cd799439012"),
        "alias": "complete_model",
        "name": "Complete Model",
        "type": "ResNet",
        "status": "active",
        "accuracy": 0.96,
        "version": "2.0",
        "created_at": "2024-01-01",
        "updated_at": "2024-06-01",
        "description": "A complete model with all fields",
        "parameters": 25000000,
        "architecture": {"layers": 50, "input_size": [224, 224, 3]},
        "metadata": {"framework": "PyTorch", "training_dataset": "ImageNet"},
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_alias_service(alias)

        assert result["alias"] == "complete_model"
        assert result["accuracy"] == 0.96
        assert result["version"] == "2.0"
        assert result["description"] == "A complete model with all fields"
        assert result["parameters"] == 25000000
        assert result["architecture"]["layers"] == 50
        assert result["metadata"]["framework"] == "PyTorch"


@pytest.mark.asyncio
async def test_get_model_by_alias_database_error():
    """Test handling of database errors"""
    alias = "test_model"

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(
        side_effect=Exception("Database connection failed")
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_alias_service(alias)

        assert exc_info.value.status_code == 500
        assert "Failed to fetch model" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_model_by_alias_special_characters():
    """Test fetching models with special characters in alias"""
    aliases = ["resnet-50", "vgg_16", "efficientnet.b0", "mobilenet v2"]

    for alias in aliases:
        mock_model = {
            "_id": ObjectId(),
            "model_id": ObjectId(),
            "alias": alias,
            "name": f"Model {alias}",
            "type": "CNN",
        }

        mock_db_conn = MagicMock()
        mock_db_conn.models_collection = MagicMock()
        mock_db_conn.models_collection.find_one = AsyncMock(
            return_value=mock_model.copy()
        )

        with patch("services.prediction_service.db_conn", mock_db_conn):
            result = await get_model_by_alias_service(alias)

            assert result["alias"] == alias
            mock_db_conn.models_collection.find_one.assert_awaited_once_with(
                {"alias": alias}
            )


@pytest.mark.asyncio
async def test_get_model_by_alias_case_sensitive():
    """Test that alias search is case-sensitive"""
    alias = "DenseNet121"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId("507f1f77bcf86cd799439012"),
        "alias": "DenseNet121",
        "name": "DenseNet-121",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_alias_service(alias)

        assert result["alias"] == "DenseNet121"
        mock_db_conn.models_collection.find_one.assert_awaited_once_with(
            {"alias": "DenseNet121"}
        )


@pytest.mark.asyncio
async def test_get_model_by_alias_different_statuses():
    """Test fetching models with different status values"""
    statuses = ["active", "deprecated", "testing", "archived"]

    for status in statuses:
        alias = f"model_{status}"
        mock_model = {
            "_id": ObjectId(),
            "model_id": ObjectId(),
            "alias": alias,
            "name": f"Model {status}",
            "status": status,
        }

        mock_db_conn = MagicMock()
        mock_db_conn.models_collection = MagicMock()
        mock_db_conn.models_collection.find_one = AsyncMock(
            return_value=mock_model.copy()
        )

        with patch("services.prediction_service.db_conn", mock_db_conn):
            result = await get_model_by_alias_service(alias)

            assert result["status"] == status
            assert result["alias"] == alias


@pytest.mark.asyncio
async def test_get_model_by_alias_endpoint_response_format():
    """Test the endpoint returns proper response format"""
    alias = "test_model"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId("507f1f77bcf86cd799439012"),
        "alias": "test_model",
        "name": "Test Model",
        "type": "CNN",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        model = await get_model_by_alias_service(alias)
        response = {"model": model}

        assert "model" in response
        assert isinstance(response["model"], dict)
        assert response["model"]["alias"] == "test_model"


@pytest.mark.asyncio
async def test_get_model_by_alias_empty_string():
    """Test fetching model with empty string alias"""
    alias = ""

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_alias_service(alias)

        assert exc_info.value.status_code == 404
        mock_db_conn.models_collection.find_one.assert_awaited_once_with({"alias": ""})


@pytest.mark.asyncio
async def test_get_model_by_alias_preserves_nested_objects():
    """Test that nested objects are preserved correctly"""
    alias = "complex_model"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId("507f1f77bcf86cd799439012"),
        "alias": "complex_model",
        "name": "Complex Model",
        "hyperparameters": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "optimizer": {"type": "Adam", "beta1": 0.9, "beta2": 0.999},
        },
        "metrics": {
            "train": {"accuracy": 0.95, "loss": 0.05},
            "val": {"accuracy": 0.93, "loss": 0.07},
            "test": {"accuracy": 0.92, "loss": 0.08},
        },
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_alias_service(alias)

        assert result["hyperparameters"]["learning_rate"] == 0.001
        assert result["hyperparameters"]["optimizer"]["type"] == "Adam"
        assert result["metrics"]["train"]["accuracy"] == 0.95
        assert result["metrics"]["test"]["loss"] == 0.08


@pytest.mark.asyncio
async def test_get_model_by_alias_with_arrays():
    """Test fetching model with array fields"""
    alias = "model_with_arrays"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId("507f1f77bcf86cd799439012"),
        "alias": "model_with_arrays",
        "name": "Model With Arrays",
        "tags": ["computer_vision", "classification", "production"],
        "supported_classes": ["cat", "dog", "bird", "fish"],
        "input_shape": [224, 224, 3],
        "versions": [
            {"number": "1.0", "date": "2024-01-01"},
            {"number": "1.1", "date": "2024-03-01"},
            {"number": "2.0", "date": "2024-06-01"},
        ],
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_alias_service(alias)

        assert len(result["tags"]) == 3
        assert "computer_vision" in result["tags"]
        assert len(result["supported_classes"]) == 4
        assert result["input_shape"] == [224, 224, 3]
        assert len(result["versions"]) == 3
        assert result["versions"][2]["number"] == "2.0"


@pytest.mark.asyncio
async def test_get_model_by_alias_http_exception_reraised():
    """Test that HTTPException is re-raised correctly"""
    alias = "nonexistent"

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_alias_service(alias)

        # Verify it's the 404 HTTPException, not a 500
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_get_model_by_alias_numeric_alias():
    """Test fetching model with numeric characters in alias"""
    aliases = ["resnet50", "vgg16", "efficientnet_b7", "model123"]

    for alias in aliases:
        mock_model = {
            "_id": ObjectId(),
            "model_id": ObjectId(),
            "alias": alias,
            "name": f"Model {alias}",
        }

        mock_db_conn = MagicMock()
        mock_db_conn.models_collection = MagicMock()
        mock_db_conn.models_collection.find_one = AsyncMock(
            return_value=mock_model.copy()
        )

        with patch("services.prediction_service.db_conn", mock_db_conn):
            result = await get_model_by_alias_service(alias)

            assert result["alias"] == alias


@pytest.mark.asyncio
async def test_get_model_by_alias_long_alias():
    """Test fetching model with very long alias"""
    alias = (
        "very_long_model_alias_name_that_exceeds_normal_length_for_testing_purposes_123"
    )
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId("507f1f77bcf86cd799439012"),
        "alias": alias,
        "name": "Long Alias Model",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_alias_service(alias)

        assert result["alias"] == alias
        assert isinstance(result["_id"], str)


@pytest.mark.asyncio
async def test_get_model_by_alias_concurrent_calls():
    """Test multiple concurrent calls to get_model_by_alias_service"""
    alias = "concurrent_test"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId("507f1f77bcf86cd799439012"),
        "alias": alias,
        "name": "Concurrent Test Model",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        # Simulate concurrent calls
        import asyncio

        results = await asyncio.gather(
            get_model_by_alias_service(alias),
            get_model_by_alias_service(alias),
            get_model_by_alias_service(alias),
        )

        # Verify all calls succeeded
        assert len(results) == 3
        for result in results:
            assert result["alias"] == alias
            assert isinstance(result["_id"], str)

        # Verify find_one was called 3 times
        assert mock_db_conn.models_collection.find_one.await_count == 3


@pytest.mark.asyncio
async def test_get_model_by_id_not_found():
    """Test fetching a model with non-existent ID"""
    model_id = "507f1f77bcf86cd799439012"

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_id_service(model_id)

        assert exc_info.value.status_code == 404
        assert f"Model with ID '{model_id}' not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_model_by_id_invalid_format():
    """Test fetching model with invalid ObjectId format"""
    invalid_ids = [
        "invalid_id",
        "12345",
        "not-an-objectid",
        "507f1f77bcf86cd79943901",  # too short
        "507f1f77bcf86cd799439012z",  # invalid character
        "",
        "gggggggggggggggggggggggg",  # invalid hex
    ]

    for invalid_id in invalid_ids:
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_id_service(invalid_id)

        assert exc_info.value.status_code == 400
        assert "Invalid model ID format" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_model_by_id_valid_objectid_formats():
    """Test fetching models with various valid ObjectId formats"""
    valid_ids = [
        "507f1f77bcf86cd799439011",
        "507f191e810c19729de860ea",
        "000000000000000000000000",
        "ffffffffffffffffffffffff",
        "123456789012345678901234",
    ]

    for valid_id in valid_ids:
        mock_model = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "model_id": ObjectId(valid_id),
            "name": f"Model {valid_id}",
            "type": "CNN",
        }

        mock_db_conn = MagicMock()
        mock_db_conn.models_collection = MagicMock()
        mock_db_conn.models_collection.find_one = AsyncMock(
            return_value=mock_model.copy()
        )

        with patch("services.prediction_service.db_conn", mock_db_conn):
            result = await get_model_by_id_service(valid_id)

            assert isinstance(result["_id"], str)
            assert isinstance(result["model_id"], str)


@pytest.mark.asyncio
async def test_get_model_by_id_objectid_conversion():
    """Test that ObjectId fields are properly converted to strings"""
    model_id = "507f1f77bcf86cd799439012"
    original_id = ObjectId("507f1f77bcf86cd799439011")
    original_model_id = ObjectId(model_id)

    mock_model = {
        "_id": original_id,
        "model_id": original_model_id,
        "name": "Test Model",
        "alias": "test_model",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_id_service(model_id)

        assert result["_id"] == str(original_id)
        assert result["model_id"] == str(original_model_id)
        assert result["_id"] == "507f1f77bcf86cd799439011"
        assert result["model_id"] == model_id


@pytest.mark.asyncio
async def test_get_model_by_id_without_model_id_field():
    """Test fetching a model document that doesn't have model_id field"""
    model_id = "507f1f77bcf86cd799439012"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "Model Without ID Field",
        "alias": "no_id_model",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_id_service(model_id)

        assert isinstance(result["_id"], str)
        assert "model_id" not in result


@pytest.mark.asyncio
async def test_get_model_by_id_http_exception_reraised_invalid_id():
    """Test that HTTPException is re-raised correctly"""
    invalid_id = "invalid"

    with pytest.raises(HTTPException) as exc_info:
        await get_model_by_id_service(invalid_id)

    # Verify it's the 400 HTTPException, not a 500
    assert exc_info.value.status_code == 400
    assert "Invalid model ID format" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_model_by_id_query_uses_string():
    """Test that the database query uses the string model_id, not ObjectId"""
    model_id = "507f1f77bcf86cd799439012"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId(model_id),
        "name": "Test Model",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        await get_model_by_id_service(model_id)

        # Verify the query was made with string, not ObjectId
        call_args = mock_db_conn.models_collection.find_one.call_args
        query = call_args[0][0]
        assert query == {"model_id": model_id}
        assert isinstance(query["model_id"], str)


@pytest.mark.asyncio
async def test_get_model_by_id_concurrent_calls():
    """Test multiple concurrent calls to get_model_by_id_service"""
    model_id = "507f1f77bcf86cd799439012"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId(model_id),
        "name": "Concurrent Test Model",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        import asyncio

        results = await asyncio.gather(
            get_model_by_id_service(model_id),
            get_model_by_id_service(model_id),
            get_model_by_id_service(model_id),
        )

        assert len(results) == 3
        for result in results:
            assert isinstance(result["_id"], str)
            assert isinstance(result["model_id"], str)

        assert mock_db_conn.models_collection.find_one.await_count == 3


@pytest.mark.asyncio
async def test_get_model_by_id_uppercase_hex():
    """Test fetching model with uppercase hex in ObjectId"""
    model_id_lower = "507f1f77bcf86cd799439012"
    model_id_upper = "507F1F77BCF86CD799439012"

    # ObjectId should handle both cases
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId(model_id_lower),
        "name": "Test Model",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        # Test with uppercase
        result = await get_model_by_id_service(model_id_upper)
        assert isinstance(result["_id"], str)


@pytest.mark.asyncio
async def test_get_model_by_id_validation_before_query():
    """Test that ObjectId validation happens before database query"""
    invalid_id = "invalid_id"

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock()

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_id_service(invalid_id)

        # Verify validation error occurred
        assert exc_info.value.status_code == 400

        # Verify database was never queried
        mock_db_conn.models_collection.find_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_model_by_id_multiple_different_ids():
    """Test fetching multiple different models by their IDs"""
    model_ids = [
        "507f1f77bcf86cd799439011",
        "507f1f77bcf86cd799439012",
        "507f1f77bcf86cd799439013",
        "507f1f77bcf86cd799439014",
    ]

    for model_id in model_ids:
        mock_model = {
            "_id": ObjectId(),
            "model_id": ObjectId(model_id),
            "name": f"Model {model_id}",
            "alias": f"model_{model_id[-4:]}",
        }

        mock_db_conn = MagicMock()
        mock_db_conn.models_collection = MagicMock()
        mock_db_conn.models_collection.find_one = AsyncMock(
            return_value=mock_model.copy()
        )

        with patch("services.prediction_service.db_conn", mock_db_conn):
            result = await get_model_by_id_service(model_id)

            assert result["model_id"] == model_id
            assert isinstance(result["_id"], str)


@pytest.mark.asyncio
async def test_get_model_by_id_none_values():
    """Test fetching model with None values in fields"""
    model_id = "507f1f77bcf86cd799439012"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId(model_id),
        "name": "Test Model",
        "description": None,
        "version": None,
        "accuracy": 0.95,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_id_service(model_id)

        assert result["description"] is None
        assert result["version"] is None
        assert result["accuracy"] == 0.95


@pytest.mark.asyncio
async def test_get_model_by_id_success():
    """Test successfully fetching a model by ID"""
    model_id = "507f1f77bcf86cd799439012"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId(model_id),
        "alias": "resnet50",
        "name": "ResNet-50",
        "type": "ResNet",
        "status": "active",
        "accuracy": 0.95,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_id_service(model_id)

        assert result["name"] == "ResNet-50"
        assert result["type"] == "ResNet"
        assert result["status"] == "active"
        assert isinstance(result["_id"], str)
        assert isinstance(result["model_id"], str)
        assert result["model_id"] == model_id

        mock_db_conn.models_collection.find_one.assert_awaited_once_with(
            {"model_id": model_id}
        )


@pytest.mark.asyncio
async def test_get_model_by_id_invalid_objectid_format():
    """Test fetching model with invalid ObjectId format"""
    invalid_ids = [
        "invalid_id",
        "12345",
        "not-an-objectid",
        "zzzzzzzzzzzzzzzzzzzzzzz",
        "507f1f77bcf86cd79943901",  # too short
        "507f1f77bcf86cd799439012345",  # too long
        "",
    ]

    for invalid_id in invalid_ids:
        mock_db_conn = MagicMock()

        with patch("services.prediction_service.db_conn", mock_db_conn):
            with pytest.raises(HTTPException) as exc_info:
                await get_model_by_id_service(invalid_id)

            assert exc_info.value.status_code == 400
            assert "Invalid model ID format" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_model_by_id_multiple_valid_ids():
    """Test fetching different models by various valid IDs"""
    model_ids = [
        "507f1f77bcf86cd799439011",
        "507f1f77bcf86cd799439022",
        "507f1f77bcf86cd799439033",
        "507f1f77bcf86cd799439044",
    ]

    for model_id in model_ids:
        mock_model = {
            "_id": ObjectId(),
            "model_id": ObjectId(model_id),
            "alias": f"model_{model_id[-4:]}",
            "name": f"Model {model_id[-4:]}",
            "type": "CNN",
        }

        mock_db_conn = MagicMock()
        mock_db_conn.models_collection = MagicMock()
        mock_db_conn.models_collection.find_one = AsyncMock(
            return_value=mock_model.copy()
        )

        with patch("services.prediction_service.db_conn", mock_db_conn):
            result = await get_model_by_id_service(model_id)

            assert result["model_id"] == model_id
            assert isinstance(result["_id"], str)
            assert isinstance(result["model_id"], str)


@pytest.mark.asyncio
async def test_get_model_by_id_with_all_fields():
    """Test fetching a model with all possible fields"""
    model_id = "507f1f77bcf86cd799439014"
    mock_model = {
        "_id": ObjectId("68dbf6a60301e94f6210b3dd"),
        "model_id": ObjectId(model_id),
        "name": "ResNet-50",
        "alias": "resnet50",
        "type": "ResNet",
        "version": "v1.3",
        "description": "Deep residual network with 50 layers. Proven architecture for image classification with excellent performance on plant disease datasets.",
        "accuracy": 0.9898,
        "status": "active",
        "deployment": {
            "endpoint_url": "http://api.myapp.com/models/resnet50",
            "framework": "PyTorch",
            "device": "CPU",
        },
        "created_at": "2025-09-08T14:00:00Z",
        "updated_at": "2025-09-27T11:45:00Z",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_id_service(model_id)

        assert result["model_id"] == model_id
        assert result["name"] == "ResNet-50"
        assert result["alias"] == "resnet50"
        assert result["type"] == "ResNet"
        assert result["accuracy"] == 0.9898
        assert result["version"] == "v1.3"
        assert (
            result["description"]
            == "Deep residual network with 50 layers. Proven architecture for image classification with excellent performance on plant disease datasets."
        )
        assert result["status"] == "active"
        assert (
            result["deployment"]["endpoint_url"]
            == "http://api.myapp.com/models/resnet50"
        )
        assert result["deployment"]["framework"] == "PyTorch"
        assert result["deployment"]["device"] == "CPU"
        assert result["created_at"] == "2025-09-08T14:00:00Z"
        assert result["updated_at"] == "2025-09-27T11:45:00Z"


@pytest.mark.asyncio
async def test_get_model_by_id_database_error():
    """Test handling of database errors"""
    model_id = "507f1f77bcf86cd799439012"

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(
        side_effect=Exception("Database connection failed")
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_id_service(model_id)

        assert exc_info.value.status_code == 500
        assert "Failed to fetch model" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_model_by_id_different_statuses():
    """Test fetching models with different status values"""
    statuses = ["active", "deprecated", "testing", "archived", "experimental"]

    for idx, status in enumerate(statuses):
        model_id = f"507f1f77bcf86cd79943{str(idx).zfill(4)}"
        mock_model = {
            "_id": ObjectId(),
            "model_id": ObjectId(model_id),
            "alias": f"model_{status}",
            "name": f"Model {status}",
            "status": status,
        }

        mock_db_conn = MagicMock()
        mock_db_conn.models_collection = MagicMock()
        mock_db_conn.models_collection.find_one = AsyncMock(
            return_value=mock_model.copy()
        )

        with patch("services.prediction_service.db_conn", mock_db_conn):
            result = await get_model_by_id_service(model_id)

            assert result["status"] == status
            assert result["model_id"] == model_id


@pytest.mark.asyncio
async def test_get_model_by_id_endpoint_response_format():
    """Test the endpoint returns proper response format"""
    model_id = "507f1f77bcf86cd799439012"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId(model_id),
        "alias": "test_model",
        "name": "Test Model",
        "type": "CNN",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        model = await get_model_by_id_service(model_id)
        response = {"model": model}

        assert "model" in response
        assert isinstance(response["model"], dict)
        assert response["model"]["model_id"] == model_id


@pytest.mark.asyncio
async def test_get_model_by_id_preserves_nested_objects():
    """Test that nested objects are preserved correctly"""
    model_id = "507f1f77bcf86cd799439012"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId(model_id),
        "alias": "complex_model",
        "name": "Complex Model",
        "hyperparameters": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "optimizer": {"type": "Adam", "beta1": 0.9, "beta2": 0.999},
        },
        "metrics": {
            "train": {"accuracy": 0.95, "loss": 0.05},
            "val": {"accuracy": 0.93, "loss": 0.07},
            "test": {"accuracy": 0.92, "loss": 0.08},
        },
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_id_service(model_id)

        assert result["hyperparameters"]["learning_rate"] == 0.001
        assert result["hyperparameters"]["optimizer"]["type"] == "Adam"
        assert result["metrics"]["train"]["accuracy"] == 0.95
        assert result["metrics"]["test"]["loss"] == 0.08


@pytest.mark.asyncio
async def test_get_model_by_id_with_arrays():
    """Test fetching model with array fields"""
    model_id = "507f1f77bcf86cd799439012"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId(model_id),
        "alias": "model_with_arrays",
        "name": "Model With Arrays",
        "tags": ["computer_vision", "classification", "production"],
        "supported_classes": ["cat", "dog", "bird", "fish"],
        "input_shape": [224, 224, 3],
        "versions": [
            {"number": "1.0", "date": "2024-01-01"},
            {"number": "1.1", "date": "2024-03-01"},
            {"number": "2.0", "date": "2024-06-01"},
        ],
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_id_service(model_id)

        assert len(result["tags"]) == 3
        assert "computer_vision" in result["tags"]
        assert len(result["supported_classes"]) == 4
        assert result["input_shape"] == [224, 224, 3]
        assert len(result["versions"]) == 3
        assert result["versions"][2]["number"] == "2.0"


@pytest.mark.asyncio
async def test_get_model_by_id_http_exception_reraised():
    """Test that HTTPException is re-raised correctly"""
    model_id = "507f1f77bcf86cd799439999"

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_id_service(model_id)

        # Verify it's the 404 HTTPException, not a 500
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_get_model_by_id_uppercase_objectid():
    """Test fetching model with uppercase ObjectId characters"""
    model_id = "507F1F77BCF86CD799439012"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId(model_id.lower()),
        "alias": "test_model",
        "name": "Test Model",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_id_service(model_id)

        assert isinstance(result["_id"], str)
        assert isinstance(result["model_id"], str)


@pytest.mark.asyncio
async def test_get_model_by_id_query_uses_string_not_objectid():
    """Test that the query uses string model_id, not ObjectId"""
    model_id = "507f1f77bcf86cd799439012"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId(model_id),
        "alias": "test_model",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        await get_model_by_id_service(model_id)

        # Verify the query uses the string ID, not ObjectId(model_id)
        call_args = mock_db_conn.models_collection.find_one.call_args
        assert call_args[0][0] == {"model_id": model_id}
        assert isinstance(call_args[0][0]["model_id"], str)


@pytest.mark.asyncio
async def test_get_model_by_id_objectid_validation_before_query():
    """Test that ObjectId validation happens before database query"""
    invalid_id = "invalid_id_format"

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_id_service(invalid_id)

        assert exc_info.value.status_code == 400
        # Verify database was never queried
        mock_db_conn.models_collection.find_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_model_by_id_all_zeros_objectid():
    """Test with valid ObjectId format but all zeros"""
    model_id = "000000000000000000000000"

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_id_service(model_id)

        # Should pass validation but return 404
        assert exc_info.value.status_code == 404
        mock_db_conn.models_collection.find_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_model_by_id_all_fs_objectid():
    """Test with valid ObjectId format but all F's"""
    model_id = "ffffffffffffffffffffffff"

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_by_id_service(model_id)

        # Should pass validation but return 404
        assert exc_info.value.status_code == 404
        mock_db_conn.models_collection.find_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_model_by_id_mixed_case_objectid():
    """Test with mixed case ObjectId"""
    model_id = "507f1F77BcF86Cd799439012"
    mock_model = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "model_id": ObjectId(model_id.lower()),
        "alias": "test_model",
        "name": "Test Model",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.models_collection = MagicMock()
    mock_db_conn.models_collection.find_one = AsyncMock(return_value=mock_model.copy())

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_model_by_id_service(model_id)

        assert isinstance(result["_id"], str)
        assert isinstance(result["model_id"], str)


@pytest.mark.asyncio
async def test_get_model_by_id_different_model_types():
    """Test fetching models of different types"""
    model_types = ["CNN", "ResNet", "VGG", "EfficientNet", "MobileNet", "DenseNet"]

    for idx, model_type in enumerate(model_types):
        model_id = f"507f1f77bcf86cd79943{str(idx).zfill(4)}"
        mock_model = {
            "_id": ObjectId(),
            "model_id": ObjectId(model_id),
            "alias": f"{model_type.lower()}_model",
            "name": f"{model_type} Model",
            "type": model_type,
        }

        mock_db_conn = MagicMock()
        mock_db_conn.models_collection = MagicMock()
        mock_db_conn.models_collection.find_one = AsyncMock(
            return_value=mock_model.copy()
        )

        with patch("services.prediction_service.db_conn", mock_db_conn):
            result = await get_model_by_id_service(model_id)

            assert result["type"] == model_type
            assert result["model_id"] == model_id
