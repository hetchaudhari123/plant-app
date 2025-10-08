import pytest
from bson import ObjectId
from datetime import datetime, timezone
from services.prediction_service import (
    get_user_predictions,
    delete_prediction,
    parse_top_predictions,
    predict_service,
)
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from fastapi import HTTPException, UploadFile
import json
import io


@pytest.mark.asyncio
async def test_get_user_predictions_success():
    """Test successful retrieval of user predictions with default pagination"""
    user_id = "user_123"

    mock_predictions = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": user_id,
            "prediction": "Positive",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439012"),
            "user_id": user_id,
            "prediction": "Negative",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_predictions.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=2)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_user_predictions(user_id=user_id)

        assert len(result["predictions"]) == 2
        assert result["total"] == 2
        assert result["skip"] == 0
        assert result["limit"] == 5

        # Check ObjectId conversion
        assert isinstance(result["predictions"][0]["_id"], str)
        assert result["predictions"][0]["_id"] == "507f1f77bcf86cd799439011"

        # Verify query and sorting
        mock_db_conn.predictions_collection.find.assert_called_once_with(
            {"user_id": user_id}
        )
        mock_cursor.sort.assert_called_once_with("created_at", -1)
        mock_cursor.skip.assert_called_once_with(0)
        mock_cursor.limit.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_get_user_predictions_custom_pagination():
    """Test predictions with custom skip and limit values"""
    user_id = "user_123"
    skip = 10
    limit = 20

    mock_predictions = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": user_id,
            "prediction": "Positive",
        }
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_predictions.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=50)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_user_predictions(user_id=user_id, skip=skip, limit=limit)

        assert result["skip"] == 10
        assert result["limit"] == 20
        assert result["total"] == 50

        mock_cursor.skip.assert_called_once_with(10)
        mock_cursor.limit.assert_called_once_with(20)


@pytest.mark.asyncio
async def test_get_user_predictions_custom_sorting():
    """Test predictions with custom sort field and order"""
    user_id = "user_123"
    sort_by = "prediction"
    sort_order = 1  # Ascending

    mock_predictions = []

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_predictions)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=0)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        await get_user_predictions(
            user_id=user_id, sort_by=sort_by, sort_order=sort_order
        )

        mock_cursor.sort.assert_called_once_with("prediction", 1)


@pytest.mark.asyncio
async def test_get_user_predictions_empty_result():
    """Test when user has no predictions"""
    user_id = "user_123"

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=0)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_user_predictions(user_id=user_id)

        assert result["predictions"] == []
        assert result["total"] == 0
        assert result["skip"] == 0
        assert result["limit"] == 5


@pytest.mark.asyncio
async def test_get_user_predictions_objectid_conversion():
    """Test that all ObjectId fields are converted to strings"""
    user_id = "user_123"

    mock_predictions = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": user_id,
            "model_id": ObjectId("507f1f77bcf86cd799439022"),
            "reference_id": ObjectId("507f1f77bcf86cd799439033"),
            "prediction": "Positive",
        }
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_predictions.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=1)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_user_predictions(user_id=user_id)

        prediction = result["predictions"][0]

        # Check all ObjectId fields are converted to strings
        assert isinstance(prediction["_id"], str)
        assert prediction["_id"] == "507f1f77bcf86cd799439011"
        assert isinstance(prediction["model_id"], str)
        assert prediction["model_id"] == "507f1f77bcf86cd799439022"
        assert isinstance(prediction["reference_id"], str)
        assert prediction["reference_id"] == "507f1f77bcf86cd799439033"

        # Non-ObjectId fields remain unchanged
        assert prediction["user_id"] == user_id
        assert prediction["prediction"] == "Positive"


@pytest.mark.asyncio
async def test_get_user_predictions_no_objectid_fields():
    """Test predictions without any ObjectId fields"""
    user_id = "user_123"

    mock_predictions = [{"user_id": user_id, "prediction": "Positive", "score": 0.95}]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_predictions.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=1)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_user_predictions(user_id=user_id)

        # Should not raise any errors
        assert len(result["predictions"]) == 1
        assert result["predictions"][0]["user_id"] == user_id


@pytest.mark.asyncio
async def test_get_user_predictions_descending_sort():
    """Test predictions with descending sort order"""
    user_id = "user_123"

    mock_predictions = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "user_id": user_id,
            "created_at": datetime(2025, 1, 3),
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439012"),
            "user_id": user_id,
            "created_at": datetime(2025, 1, 2),
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": user_id,
            "created_at": datetime(2025, 1, 1),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_predictions.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=3)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_user_predictions(
            user_id=user_id, sort_by="created_at", sort_order=-1
        )

        mock_cursor.sort.assert_called_once_with("created_at", -1)
        assert len(result["predictions"]) == 3


@pytest.mark.asyncio
async def test_get_user_predictions_ascending_sort():
    """Test predictions with ascending sort order"""
    user_id = "user_123"

    mock_predictions = []

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_predictions)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=0)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        await get_user_predictions(user_id=user_id, sort_by="created_at", sort_order=1)

        mock_cursor.sort.assert_called_once_with("created_at", 1)


@pytest.mark.asyncio
async def test_get_user_predictions_large_dataset():
    """Test pagination with a large dataset"""
    user_id = "user_123"

    # Simulate large dataset with only 5 results per page
    mock_predictions = [
        {
            "_id": ObjectId(f"507f1f77bcf86cd79943901{i}"),
            "user_id": user_id,
            "prediction": f"Prediction {i}",
        }
        for i in range(5)
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_predictions.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=1000)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_user_predictions(user_id=user_id, skip=0, limit=5)

        assert len(result["predictions"]) == 5
        assert result["total"] == 1000
        assert result["skip"] == 0
        assert result["limit"] == 5


@pytest.mark.asyncio
async def test_get_user_predictions_second_page():
    """Test fetching the second page of results"""
    user_id = "user_123"

    mock_predictions = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439016"),
            "user_id": user_id,
            "prediction": "Prediction 6",
        }
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_predictions.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=10)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_user_predictions(user_id=user_id, skip=5, limit=5)

        mock_cursor.skip.assert_called_once_with(5)
        assert result["skip"] == 5
        assert result["total"] == 10


@pytest.mark.asyncio
async def test_get_user_predictions_mixed_data_types():
    """Test predictions with various data types including nested ObjectIds"""
    user_id = "user_123"

    mock_predictions = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": user_id,
            "prediction": "Positive",
            "score": 0.95,
            "tags": ["tag1", "tag2"],
            "metadata": {
                "nested_id": ObjectId("507f1f77bcf86cd799439099"),
                "count": 10,
            },
        }
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_predictions.copy())

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=1)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await get_user_predictions(user_id=user_id)

        prediction = result["predictions"][0]

        # Check top-level ObjectId conversion
        assert isinstance(prediction["_id"], str)

        # Check non-ObjectId fields remain unchanged
        assert prediction["score"] == 0.95
        assert prediction["tags"] == ["tag1", "tag2"]

        # Note: Nested ObjectIds in dicts won't be converted by current implementation
        # This test documents the current behavior
        assert isinstance(prediction["metadata"]["nested_id"], ObjectId)


@pytest.mark.asyncio
async def test_get_user_predictions_query_parameters():
    """Test that correct query parameters are used"""
    user_id = "user_456"

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_db_conn.predictions_collection.count_documents = AsyncMock(return_value=0)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        await get_user_predictions(user_id=user_id)

        # Verify find was called with correct user_id
        mock_db_conn.predictions_collection.find.assert_called_once_with(
            {"user_id": "user_456"}
        )

        # Verify count_documents was called with same filter
        mock_db_conn.predictions_collection.count_documents.assert_called_once_with(
            {"user_id": "user_456"}
        )


@pytest.mark.asyncio
async def test_delete_prediction_success_with_user_id():
    """Test successful deletion of prediction with user_id verification"""
    prediction_id = "pred_123"
    user_id = "user_456"

    mock_existing_prediction = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "prediction_id": prediction_id,
        "user_id": user_id,
        "prediction": "Positive",
    }

    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(
        return_value=mock_existing_prediction
    )
    mock_db_conn.predictions_collection.delete_one = AsyncMock(
        return_value=mock_delete_result
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await delete_prediction(prediction_id=prediction_id, user_id=user_id)

        assert result["success"] is True
        assert result["message"] == "Prediction deleted successfully"
        assert result["prediction_id"] == prediction_id

        # Verify find_one was called with correct filter
        mock_db_conn.predictions_collection.find_one.assert_called_once_with(
            {"prediction_id": prediction_id, "user_id": user_id}
        )

        # Verify delete_one was called with correct filter
        mock_db_conn.predictions_collection.delete_one.assert_called_once_with(
            {"prediction_id": prediction_id, "user_id": user_id}
        )


@pytest.mark.asyncio
async def test_delete_prediction_success_without_user_id():
    """Test successful deletion of prediction without user_id verification"""
    prediction_id = "pred_123"

    mock_existing_prediction = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "prediction_id": prediction_id,
        "user_id": "some_user",
        "prediction": "Positive",
    }

    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(
        return_value=mock_existing_prediction
    )
    mock_db_conn.predictions_collection.delete_one = AsyncMock(
        return_value=mock_delete_result
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await delete_prediction(prediction_id=prediction_id, user_id=None)

        assert result["success"] is True
        assert result["message"] == "Prediction deleted successfully"
        assert result["prediction_id"] == prediction_id

        # Verify find_one was called without user_id in filter
        mock_db_conn.predictions_collection.find_one.assert_called_once_with(
            {"prediction_id": prediction_id}
        )

        # Verify delete_one was called without user_id in filter
        mock_db_conn.predictions_collection.delete_one.assert_called_once_with(
            {"prediction_id": prediction_id}
        )


@pytest.mark.asyncio
async def test_delete_prediction_not_found_with_user_id():
    """Test error when prediction not found or doesn't belong to user"""
    prediction_id = "pred_123"
    user_id = "user_456"

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(ValueError) as exc_info:
            await delete_prediction(prediction_id=prediction_id, user_id=user_id)

        assert str(exc_info.value) == "Prediction not found or does not belong to user"

        # Verify find_one was called
        mock_db_conn.predictions_collection.find_one.assert_called_once_with(
            {"prediction_id": prediction_id, "user_id": user_id}
        )

        # Verify delete_one was NOT called
        mock_db_conn.predictions_collection.delete_one.assert_not_called()


@pytest.mark.asyncio
async def test_delete_prediction_not_found_without_user_id():
    """Test error when prediction not found (no user_id provided)"""
    prediction_id = "pred_123"

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(ValueError) as exc_info:
            await delete_prediction(prediction_id=prediction_id, user_id=None)

        assert str(exc_info.value) == f"Prediction with id {prediction_id} not found"

        # Verify delete_one was NOT called
        mock_db_conn.predictions_collection.delete_one.assert_not_called()


@pytest.mark.asyncio
async def test_delete_prediction_delete_fails():
    """Test error when delete operation fails (deleted_count != 1)"""
    prediction_id = "pred_123"
    user_id = "user_456"

    mock_existing_prediction = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "prediction_id": prediction_id,
        "user_id": user_id,
    }

    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 0  # Deletion failed

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(
        return_value=mock_existing_prediction
    )
    mock_db_conn.predictions_collection.delete_one = AsyncMock(
        return_value=mock_delete_result
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(ValueError) as exc_info:
            await delete_prediction(prediction_id=prediction_id, user_id=user_id)

        assert (
            str(exc_info.value)
            == f"Failed to delete prediction with id {prediction_id}"
        )

        # Verify both find_one and delete_one were called
        mock_db_conn.predictions_collection.find_one.assert_called_once()
        mock_db_conn.predictions_collection.delete_one.assert_called_once()


@pytest.mark.asyncio
async def test_delete_prediction_wrong_user():
    """Test that user cannot delete another user's prediction"""
    prediction_id = "pred_123"
    requesting_user_id = "user_456"

    # Prediction belongs to different user
    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(ValueError) as exc_info:
            await delete_prediction(
                prediction_id=prediction_id, user_id=requesting_user_id
            )

        assert str(exc_info.value) == "Prediction not found or does not belong to user"

        # Verify the filter included both prediction_id and user_id
        mock_db_conn.predictions_collection.find_one.assert_called_once_with(
            {"prediction_id": prediction_id, "user_id": requesting_user_id}
        )


@pytest.mark.asyncio
async def test_delete_prediction_query_filter_structure():
    """Test that query filter is built correctly based on user_id presence"""
    prediction_id = "pred_789"
    user_id = "user_999"

    mock_existing_prediction = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "prediction_id": prediction_id,
        "user_id": user_id,
    }

    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(
        return_value=mock_existing_prediction
    )
    mock_db_conn.predictions_collection.delete_one = AsyncMock(
        return_value=mock_delete_result
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        await delete_prediction(prediction_id=prediction_id, user_id=user_id)

        # Get the actual call arguments
        find_one_call_args = mock_db_conn.predictions_collection.find_one.call_args[0][
            0
        ]
        delete_one_call_args = mock_db_conn.predictions_collection.delete_one.call_args[
            0
        ][0]

        # Verify filter structure
        assert "prediction_id" in find_one_call_args
        assert "user_id" in find_one_call_args
        assert find_one_call_args["prediction_id"] == prediction_id
        assert find_one_call_args["user_id"] == user_id

        assert find_one_call_args == delete_one_call_args


@pytest.mark.asyncio
async def test_delete_prediction_multiple_deleted_count():
    """Test that ValueError is raised when deleted_count > 1"""
    prediction_id = "pred_123"
    user_id = "user_456"

    mock_existing_prediction = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "prediction_id": prediction_id,
        "user_id": user_id,
    }

    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 2  # simulate unexpected multiple deletions

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(
        return_value=mock_existing_prediction
    )
    mock_db_conn.predictions_collection.delete_one = AsyncMock(
        return_value=mock_delete_result
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(
            ValueError, match=f"Failed to delete prediction with id {prediction_id}"
        ):
            await delete_prediction(prediction_id=prediction_id, user_id=user_id)


@pytest.mark.asyncio
async def test_delete_prediction_empty_prediction_id():
    """Test deletion with empty prediction_id string"""
    prediction_id = ""
    user_id = "user_456"

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(return_value=None)

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(ValueError):
            await delete_prediction(prediction_id=prediction_id, user_id=user_id)

        # Verify find_one was still called with empty string
        mock_db_conn.predictions_collection.find_one.assert_called_once_with(
            {"prediction_id": "", "user_id": user_id}
        )


@pytest.mark.asyncio
async def test_delete_prediction_with_special_characters():
    """Test deletion with prediction_id containing special characters"""
    prediction_id = "pred_123-abc@xyz"
    user_id = "user_456"

    mock_existing_prediction = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "prediction_id": prediction_id,
        "user_id": user_id,
    }

    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(
        return_value=mock_existing_prediction
    )
    mock_db_conn.predictions_collection.delete_one = AsyncMock(
        return_value=mock_delete_result
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await delete_prediction(prediction_id=prediction_id, user_id=user_id)

        assert result["success"] is True
        assert result["prediction_id"] == prediction_id


@pytest.mark.asyncio
async def test_delete_prediction_database_error_on_find():
    """Test handling of database errors during find_one operation"""
    prediction_id = "pred_123"
    user_id = "user_456"

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(
        side_effect=Exception("Database connection error")
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(Exception) as exc_info:
            await delete_prediction(prediction_id=prediction_id, user_id=user_id)

        assert "Database connection error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_prediction_database_error_on_delete():
    """Test handling of database errors during delete_one operation"""
    prediction_id = "pred_123"
    user_id = "user_456"

    mock_existing_prediction = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "prediction_id": prediction_id,
        "user_id": user_id,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(
        return_value=mock_existing_prediction
    )
    mock_db_conn.predictions_collection.delete_one = AsyncMock(
        side_effect=Exception("Database write error")
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        with pytest.raises(Exception) as exc_info:
            await delete_prediction(prediction_id=prediction_id, user_id=user_id)

        assert "Database write error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_prediction_return_structure():
    """Test that the return structure contains all expected fields"""
    prediction_id = "pred_123"
    user_id = "user_456"

    mock_existing_prediction = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "prediction_id": prediction_id,
        "user_id": user_id,
    }

    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(
        return_value=mock_existing_prediction
    )
    mock_db_conn.predictions_collection.delete_one = AsyncMock(
        return_value=mock_delete_result
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await delete_prediction(prediction_id=prediction_id, user_id=user_id)

        # Verify all expected keys are present
        assert "success" in result
        assert "message" in result
        assert "prediction_id" in result

        # Verify types
        assert isinstance(result["success"], bool)
        assert isinstance(result["message"], str)
        assert isinstance(result["prediction_id"], str)


@pytest.mark.asyncio
async def test_delete_prediction_none_user_id_explicitly():
    """Test deletion with user_id explicitly set to None"""
    prediction_id = "pred_123"

    mock_existing_prediction = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "prediction_id": prediction_id,
        "user_id": "some_user",
    }

    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(
        return_value=mock_existing_prediction
    )
    mock_db_conn.predictions_collection.delete_one = AsyncMock(
        return_value=mock_delete_result
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):

        # Verify user_id was not added to filter
        find_call_args = mock_db_conn.predictions_collection.find_one.call_args[0][0]
        assert "user_id" not in find_call_args
        assert "prediction_id" in find_call_args


@pytest.mark.asyncio
async def test_delete_prediction_uuid_format():
    """Test deletion with UUID format prediction_id"""
    prediction_id = "550e8400-e29b-41d4-a716-446655440000"
    user_id = "user_456"

    mock_existing_prediction = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "prediction_id": prediction_id,
        "user_id": user_id,
    }

    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.find_one = AsyncMock(
        return_value=mock_existing_prediction
    )
    mock_db_conn.predictions_collection.delete_one = AsyncMock(
        return_value=mock_delete_result
    )

    with patch("services.prediction_service.db_conn", mock_db_conn):
        result = await delete_prediction(prediction_id=prediction_id, user_id=user_id)

        assert result["success"] is True
        assert result["prediction_id"] == prediction_id


@pytest.mark.asyncio
async def test_predict_service_success():
    """Test successful prediction with all components working"""
    model_name = "mobilenet_v3_large"
    user_id = "user_123"
    top_k = 5

    # Mock file
    mock_file_content = b"fake image content"
    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = io.BytesIO(mock_file_content)
    mock_file.filename = "test_image.jpg"

    # Mock idx2label mapping
    mock_idx2label = {
        "0": "apple/apple scab",
        "1": "apple/black rot",
        "2": "tomato/early blight",
    }

    # Mock Cloudinary upload result
    mock_cloudinary_result = {
        "secure_url": "https://cloudinary.com/image123.jpg",
        "public_id": "plant_app/plant_images/image123",
    }

    # Mock model prediction result
    mock_prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.999808132648468,
        "raw_output": [0.999808132648468, 0.000191867351532, 0.0],
    }

    # Mock database insert result
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "507f1f77bcf86cd799439011"

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.insert_one = AsyncMock(
        return_value=mock_insert_result
    )

    mock_settings = MagicMock()
    mock_settings.PREDICTION_EXPIRY_HOURS = 24

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_idx2label))), patch(
        "services.prediction_service.cloudinary.uploader.upload",
        return_value=mock_cloudinary_result,
    ), patch(
        "services.prediction_service.get_prediction",
        new_callable=AsyncMock,
        return_value=mock_prediction_result,
    ), patch(
        "services.prediction_service.db_conn", mock_db_conn
    ), patch(
        "services.prediction_service.settings", mock_settings
    ), patch(
        "services.prediction_service.time.perf_counter", side_effect=[0.0, 0.5]
    ):

        result = await predict_service(model_name, mock_file, user_id, top_k)

        # Verify result structure
        assert result["prediction_id"] is not None
        assert result["model_name"] == model_name
        assert result["user_id"] == user_id
        assert result["image_url"] == "https://cloudinary.com/image123.jpg"
        assert result["status"] == "completed"
        assert result["crop"] == "apple"
        assert result["disease"] == "apple scab"
        assert result["processing_time"] == 0.5
        assert "_id" in result
        assert result["_id"] == "507f1f77bcf86cd799439011"

        # Verify raw_output structure
        assert "raw_output" in result
        assert "top_predictions" in result["raw_output"]
        assert len(result["raw_output"]["top_predictions"]) <= top_k
        assert result["raw_output"]["primary_confidence"] == 0.999808132648468

        # Verify database insert was called
        mock_db_conn.predictions_collection.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_predict_service_with_top_k_3():
    """Test prediction with custom top_k value"""
    model_name = "resnet50"
    user_id = "user_123"
    top_k = 3

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = io.BytesIO(b"fake image")

    mock_idx2label = {
        "0": "apple/apple scab",
        "1": "apple/black rot",
        "2": "tomato/early blight",
        "3": "tomato/late blight",
        "4": "corn/common rust",
    }

    mock_cloudinary_result = {"secure_url": "https://cloudinary.com/img.jpg"}

    mock_prediction_result = {
        "model": "resnet50",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
        "raw_output": [0.95, 0.03, 0.015, 0.004, 0.001],
    }

    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "507f1f77bcf86cd799439011"

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.insert_one = AsyncMock(
        return_value=mock_insert_result
    )

    mock_settings = MagicMock()
    mock_settings.PREDICTION_EXPIRY_HOURS = 24

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_idx2label))), patch(
        "services.prediction_service.cloudinary.uploader.upload",
        return_value=mock_cloudinary_result,
    ), patch(
        "services.prediction_service.get_prediction",
        new_callable=AsyncMock,
        return_value=mock_prediction_result,
    ), patch(
        "services.prediction_service.db_conn", mock_db_conn
    ), patch(
        "services.prediction_service.settings", mock_settings
    ), patch(
        "services.prediction_service.time.perf_counter", side_effect=[0.0, 0.3]
    ):

        result = await predict_service(model_name, mock_file, user_id, top_k)

        # Verify only top 3 predictions are returned
        assert len(result["raw_output"]["top_predictions"]) == 3

        # Verify predictions are sorted by confidence
        top_preds = result["raw_output"]["top_predictions"]
        for i in range(len(top_preds) - 1):
            assert top_preds[i]["confidence"] >= top_preds[i + 1]["confidence"]


@pytest.mark.asyncio
async def test_predict_service_cloudinary_upload_failure():
    """Test error handling when Cloudinary upload fails"""
    model_name = "mobilenet_v3_large"
    user_id = "user_123"

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = io.BytesIO(b"fake image")

    mock_idx2label = {"0": "apple/apple scab"}

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_idx2label))), patch(
        "services.prediction_service.cloudinary.uploader.upload",
        side_effect=Exception("Cloudinary error"),
    ):

        with pytest.raises(HTTPException) as exc_info:
            await predict_service(model_name, mock_file, user_id)

        assert exc_info.value.status_code == 500
        assert "Prediction failed" in exc_info.value.detail
        assert "Cloudinary error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_predict_service_model_prediction_failure():
    """Test error handling when model prediction fails"""
    model_name = "mobilenet_v3_large"
    user_id = "user_123"

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = io.BytesIO(b"fake image")

    mock_idx2label = {"0": "apple/apple scab"}
    mock_cloudinary_result = {"secure_url": "https://cloudinary.com/img.jpg"}

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_idx2label))), patch(
        "services.prediction_service.cloudinary.uploader.upload",
        return_value=mock_cloudinary_result,
    ), patch(
        "services.prediction_service.get_prediction",
        new_callable=AsyncMock,
        side_effect=Exception("Model service error"),
    ):

        with pytest.raises(HTTPException) as exc_info:
            await predict_service(model_name, mock_file, user_id)

        assert exc_info.value.status_code == 500
        assert "Model service error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_predict_service_database_insert_failure():
    """Test error handling when database insert fails"""
    model_name = "mobilenet_v3_large"
    user_id = "user_123"

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = io.BytesIO(b"fake image")

    mock_idx2label = {"0": "apple/apple scab"}
    mock_cloudinary_result = {"secure_url": "https://cloudinary.com/img.jpg"}
    mock_prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
        "raw_output": [0.95, 0.05],
    }

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.insert_one = AsyncMock(
        side_effect=Exception("Database error")
    )

    mock_settings = MagicMock()
    mock_settings.PREDICTION_EXPIRY_HOURS = 24

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_idx2label))), patch(
        "services.prediction_service.cloudinary.uploader.upload",
        return_value=mock_cloudinary_result,
    ), patch(
        "services.prediction_service.get_prediction",
        new_callable=AsyncMock,
        return_value=mock_prediction_result,
    ), patch(
        "services.prediction_service.db_conn", mock_db_conn
    ), patch(
        "services.prediction_service.settings", mock_settings
    ), patch(
        "services.prediction_service.time.perf_counter", side_effect=[0.0, 0.5]
    ):

        with pytest.raises(HTTPException) as exc_info:
            await predict_service(model_name, mock_file, user_id)

        assert exc_info.value.status_code == 500
        assert "Database error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_predict_service_idx2label_file_not_found():
    """Test error handling when idx2label file is not found"""
    model_name = "mobilenet_v3_large"
    user_id = "user_123"

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = io.BytesIO(b"fake image")

    with patch(
        "builtins.open", side_effect=FileNotFoundError("idx2label.json not found")
    ):
        with pytest.raises(HTTPException) as exc_info:
            await predict_service(model_name, mock_file, user_id)

        assert exc_info.value.status_code == 500
        assert "Prediction failed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_predict_service_file_seek_called():
    """Test that file.seek(0) is called before operations"""
    model_name = "mobilenet_v3_large"
    user_id = "user_123"

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = MagicMock()
    mock_file.file.seek = MagicMock()

    mock_idx2label = {"0": "apple/apple scab"}
    mock_cloudinary_result = {"secure_url": "https://cloudinary.com/img.jpg"}
    mock_prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
        "raw_output": [0.95, 0.05],
    }

    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "507f1f77bcf86cd799439011"

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.insert_one = AsyncMock(
        return_value=mock_insert_result
    )

    mock_settings = MagicMock()
    mock_settings.PREDICTION_EXPIRY_HOURS = 24

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_idx2label))), patch(
        "services.prediction_service.cloudinary.uploader.upload",
        return_value=mock_cloudinary_result,
    ), patch(
        "services.prediction_service.get_prediction",
        new_callable=AsyncMock,
        return_value=mock_prediction_result,
    ), patch(
        "services.prediction_service.db_conn", mock_db_conn
    ), patch(
        "services.prediction_service.settings", mock_settings
    ), patch(
        "services.prediction_service.time.perf_counter", side_effect=[0.0, 0.5]
    ):

        await predict_service(model_name, mock_file, user_id)

        # Verify seek was called twice (before cloudinary and before prediction)
        assert mock_file.file.seek.call_count == 2
        mock_file.file.seek.assert_any_call(0)


@pytest.mark.asyncio
async def test_predict_service_timestamps_and_expiry():
    """Test that created_at and expires_at are set correctly"""
    model_name = "mobilenet_v3_large"
    user_id = "user_123"

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = io.BytesIO(b"fake image")

    mock_idx2label = {"0": "apple/apple scab"}
    mock_cloudinary_result = {"secure_url": "https://cloudinary.com/img.jpg"}
    mock_prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
        "raw_output": [0.95, 0.05],
    }

    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "507f1f77bcf86cd799439011"

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.insert_one = AsyncMock(
        return_value=mock_insert_result
    )

    mock_settings = MagicMock()
    mock_settings.PREDICTION_EXPIRY_HOURS = 48

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_idx2label))), patch(
        "services.prediction_service.cloudinary.uploader.upload",
        return_value=mock_cloudinary_result,
    ), patch(
        "services.prediction_service.get_prediction",
        new_callable=AsyncMock,
        return_value=mock_prediction_result,
    ), patch(
        "services.prediction_service.db_conn", mock_db_conn
    ), patch(
        "services.prediction_service.settings", mock_settings
    ), patch(
        "services.prediction_service.time.perf_counter", side_effect=[0.0, 0.5]
    ):

        result = await predict_service(model_name, mock_file, user_id)

        # Verify timestamps exist
        assert "created_at" in result
        assert "expires_at" in result
        assert isinstance(result["created_at"], datetime)
        assert isinstance(result["expires_at"], datetime)

        # Verify expiry is approximately 48 hours from creation
        time_diff = result["expires_at"] - result["created_at"]
        assert abs(time_diff.total_seconds() - (48 * 3600)) < 1  # Within 1 second


@pytest.mark.asyncio
async def test_predict_service_uuid_generation():
    """Test that unique prediction_id is generated"""
    model_name = "mobilenet_v3_large"
    user_id = "user_123"

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = io.BytesIO(b"fake image")

    mock_idx2label = {"0": "apple/apple scab"}
    mock_cloudinary_result = {"secure_url": "https://cloudinary.com/img.jpg"}
    mock_prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
        "raw_output": [0.95, 0.05],
    }

    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "507f1f77bcf86cd799439011"

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.predictions_collection.insert_one = AsyncMock(
        return_value=mock_insert_result
    )

    mock_settings = MagicMock()
    mock_settings.PREDICTION_EXPIRY_HOURS = 24

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_idx2label))), patch(
        "services.prediction_service.cloudinary.uploader.upload",
        return_value=mock_cloudinary_result,
    ), patch(
        "services.prediction_service.get_prediction",
        new_callable=AsyncMock,
        return_value=mock_prediction_result,
    ), patch(
        "services.prediction_service.db_conn", mock_db_conn
    ), patch(
        "services.prediction_service.settings", mock_settings
    ), patch(
        "services.prediction_service.time.perf_counter", side_effect=[0.0, 0.5]
    ), patch(
        "services.prediction_service.uuid.uuid4", return_value="test-uuid-1234"
    ):

        result = await predict_service(model_name, mock_file, user_id)

        assert result["prediction_id"] == "test-uuid-1234"


def test_parse_top_predictions_success():
    """Test parsing top predictions from raw output"""
    prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
        "raw_output": [0.95, 0.03, 0.015, 0.004, 0.001],
    }

    idx2label = {
        "0": "apple/apple scab",
        "1": "apple/black rot",
        "2": "tomato/early blight",
        "3": "tomato/late blight",
        "4": "corn/common rust",
    }

    top_k = 3

    with patch(
        "services.prediction_service.parse_crop_disease",
        side_effect=[
            ("apple", "apple scab"),
            ("apple", "black rot"),
            ("tomato", "early blight"),
        ],
    ):
        result = parse_top_predictions(prediction_result, idx2label, top_k)

        assert len(result) == 3
        assert result[0]["confidence"] == 0.95
        assert result[0]["crop"] == "apple"
        assert result[0]["disease"] == "apple scab"
        assert result[0]["class_idx"] == 0

        # Verify sorted by confidence
        assert result[0]["confidence"] >= result[1]["confidence"]
        assert result[1]["confidence"] >= result[2]["confidence"]


def test_parse_top_predictions_empty_raw_output():
    """Test fallback handling when raw_output is empty"""
    prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
        "raw_output": [],
    }

    idx2label = {"0": "apple/apple scab"}

    result = parse_top_predictions(prediction_result, idx2label, 5)

    # Expect a safe fallback prediction
    assert len(result) == 1
    assert result[0]["crop"] == "apple"
    assert result[0]["disease"] == "apple scab"
    assert result[0]["confidence"] == 0.95
    assert result[0]["label"] == "apple/apple scab"
    assert result[0]["class_idx"] == 0


def test_parse_top_predictions_missing_raw_output():
    """Test fallback handling when raw_output key is missing"""
    prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
    }

    idx2label = {"0": "apple/apple scab"}

    result = parse_top_predictions(prediction_result, idx2label, 5)

    # Expect a safe fallback prediction
    assert len(result) == 1
    assert result[0]["crop"] == "apple"
    assert result[0]["disease"] == "apple scab"
    assert result[0]["confidence"] == 0.95
    assert result[0]["label"] == "apple/apple scab"
    assert result[0]["class_idx"] == 0


def test_parse_top_predictions_with_unknown_labels():
    """Test parsing when some labels are missing from idx2label"""
    prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
        "raw_output": [0.95, 0.03, 0.02],
    }

    idx2label = {
        "0": "apple/apple scab",
        # Missing "1" and "2"
    }

    with patch(
        "services.prediction_service.parse_crop_disease",
        side_effect=[
            ("apple", "apple scab"),
            ("unknown", "unknown"),
            ("unknown", "unknown"),
        ],
    ):
        result = parse_top_predictions(prediction_result, idx2label, 3)

        assert len(result) == 3
        assert result[0]["label"] == "apple/apple scab"
        assert result[1]["label"] == "unknown/unknown"
        assert result[2]["label"] == "unknown/unknown"


def test_parse_top_predictions_exception_handling():
    """Test that exceptions are caught and safe default is returned"""
    prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
        "raw_output": None,  # This will cause an error
    }

    idx2label = {"0": "apple/apple scab"}

    with patch(
        "services.prediction_service.parse_crop_disease",
        return_value=("apple", "apple scab"),
    ):
        result = parse_top_predictions(prediction_result, idx2label, 5)

        # Should return safe default with primary prediction
        assert len(result) == 1
        assert result[0]["crop"] == "apple"
        assert result[0]["disease"] == "apple scab"
        assert result[0]["confidence"] == 0.95
        assert result[0]["label"] == "apple/apple scab"
        assert result[0]["class_idx"] == 0


def test_parse_top_predictions_top_k_larger_than_results():
    """Test when top_k is larger than available predictions"""
    prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
        "raw_output": [0.95, 0.05],
    }

    idx2label = {"0": "apple/apple scab", "1": "apple/black rot"}

    top_k = 10  # Request more than available

    with patch(
        "services.prediction_service.parse_crop_disease",
        side_effect=[("apple", "apple scab"), ("apple", "black rot")],
    ):
        result = parse_top_predictions(prediction_result, idx2label, top_k)

        # Should return only available predictions
        assert len(result) == 2


def test_parse_top_predictions_confidence_conversion():
    """Test that confidence values are converted to float"""
    prediction_result = {
        "model": "mobilenet_v3_large",
        "prediction": "apple/apple scab",
        "confidence": 0.95,
        "raw_output": [0.95, 0.05],
    }

    idx2label = {"0": "apple/apple scab", "1": "apple/black rot"}

    with patch(
        "services.prediction_service.parse_crop_disease",
        side_effect=[("apple", "apple scab"), ("apple", "black rot")],
    ):
        result = parse_top_predictions(prediction_result, idx2label, 2)

        for pred in result:
            assert isinstance(pred["confidence"], float)
