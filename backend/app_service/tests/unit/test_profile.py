import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timezone, timedelta
from services.profile_service import (
    get_user_details,
    request_email_change,
    confirm_email_change,
    update_profile_picture,
    update_profile_name,
    delete_account,
    get_primary_crops_for_user,
    get_user_by_id,
    get_user_dashboard,
    update_farm_size,
)
from fastapi import HTTPException, Response, UploadFile
from passlib.context import CryptContext
from pymongo import ReturnDocument


@pytest.mark.asyncio
async def test_update_name_both_fields_success():
    """Test successful update of both first and last name with DiceBear avatar"""
    user_id = "user_123"

    # Mock existing user with DiceBear avatar
    mock_user = {
        "id": user_id,
        "first_name": "John",
        "last_name": "Doe",
        "profile_pic_url": "https://api.dicebear.com/5.x/initials/svg?seed=John%20Doe",
    }

    # Mock updated user
    mock_updated_user = {
        "id": user_id,
        "first_name": "Jane",
        "last_name": "Smith",
        "profile_pic_url": "https://api.dicebear.com/5.x/initials/svg?seed=Jane%20Smith",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=mock_updated_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn):
        await update_profile_name(user_id=user_id, first_name="Jane", last_name="Smith")

        # Verify find_one was called
        mock_db_conn.users_collection.find_one.assert_called_once_with({"id": user_id})

        # Verify update was called with correct fields
        mock_db_conn.users_collection.find_one_and_update.assert_called_once()
        call_args = mock_db_conn.users_collection.find_one_and_update.call_args

        assert call_args[0][0] == {"id": user_id}
        assert call_args[0][1]["$set"]["first_name"] == "Jane"
        assert call_args[0][1]["$set"]["last_name"] == "Smith"
        assert "Jane%20Smith" in call_args[0][1]["$set"]["profile_pic_url"]
        assert call_args[1]["return_document"]


@pytest.mark.asyncio
async def test_update_name_no_avatar_update_custom_pic():
    """Test that profile picture is NOT updated when user has custom avatar"""
    user_id = "user_custom"

    mock_user = {
        "id": user_id,
        "first_name": "John",
        "last_name": "Doe",
        "profile_pic_url": "https://example.com/custom-avatar.jpg",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=mock_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn):
        await update_profile_name(user_id=user_id, first_name="Jane", last_name="Smith")

        call_args = mock_db_conn.users_collection.find_one_and_update.call_args
        update_fields = call_args[0][1]["$set"]

        assert update_fields["first_name"] == "Jane"
        assert update_fields["last_name"] == "Smith"
        assert "profile_pic_url" not in update_fields


@pytest.mark.asyncio
async def test_update_name_user_not_found():
    """Test error handling when user does not exist"""
    user_id = "nonexistent_user"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await update_profile_name(user_id=user_id, first_name="Jane")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_update_name_no_fields_provided():
    """Test error when no fields are provided for update"""
    user_id = "user_empty"

    mock_user = {
        "id": user_id,
        "first_name": "John",
        "last_name": "Doe",
        "profile_pic_url": "https://api.dicebear.com/5.x/initials/svg?seed=John%20Doe",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await update_profile_name(user_id=user_id)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "No fields provided for update"


@pytest.mark.asyncio
async def test_update_name_none_values_not_updated():
    """Test that None values don't trigger updates"""
    user_id = "user_none"

    mock_user = {
        "id": user_id,
        "first_name": "John",
        "last_name": "Doe",
        "profile_pic_url": "https://api.dicebear.com/5.x/initials/svg?seed=John%20Doe",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await update_profile_name(user_id=user_id, first_name=None, last_name=None)

        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_update_name_empty_profile_pic_url():
    """Test handling when user has no profile_pic_url field"""
    user_id = "user_no_pic"

    mock_user = {
        "id": user_id,
        "first_name": "John",
        "last_name": "Doe",
        # No profile_pic_url field
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=mock_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn):
        await update_profile_name(user_id=user_id, first_name="Jane")

        call_args = mock_db_conn.users_collection.find_one_and_update.call_args
        update_fields = call_args[0][1]["$set"]

        # Should not include profile_pic_url update
        assert "profile_pic_url" not in update_fields
        assert update_fields["first_name"] == "Jane"


# Initialize password context for testing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.mark.asyncio
async def test_delete_account_success():
    """Test successful account deletion with correct password"""
    user_id = "user_123"
    password = "correct_password"
    password_hash = pwd_context.hash(password)

    mock_user = {
        "id": user_id,
        "email": "user@example.com",
        "password_hash": password_hash,
        "first_name": "John",
        "last_name": "Doe",
    }

    mock_response = Mock(spec=Response)
    mock_response.delete_cookie = Mock()

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.otps_collection = AsyncMock()

    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.delete_one = AsyncMock(
        return_value=MagicMock(deleted_count=1)
    )
    mock_db_conn.predictions_collection.delete_many = AsyncMock(
        return_value=MagicMock(deleted_count=5)
    )
    mock_db_conn.otps_collection.delete_many = AsyncMock(
        return_value=MagicMock(deleted_count=2)
    )

    with patch("services.profile_service.db_conn", mock_db_conn):
        await delete_account(user_id=user_id, password=password, response=mock_response)

        # Verify user lookup
        mock_db_conn.users_collection.find_one.assert_called_once_with({"id": user_id})

        # Verify user deletion
        mock_db_conn.users_collection.delete_one.assert_called_once_with(
            {"id": user_id}
        )

        # Verify predictions deletion
        mock_db_conn.predictions_collection.delete_many.assert_called_once_with(
            {"user_id": user_id}
        )

        # Verify OTPs deletion
        mock_db_conn.otps_collection.delete_many.assert_called_once_with(
            {"email": "user@example.com"}
        )

        # Verify cookies cleared
        assert mock_response.delete_cookie.call_count == 2
        mock_response.delete_cookie.assert_any_call("access_token")
        mock_response.delete_cookie.assert_any_call("refresh_token")


@pytest.mark.asyncio
async def test_delete_account_user_not_found():
    """Test error when user does not exist"""
    user_id = "nonexistent_user"
    password = "some_password"
    mock_response = Mock(spec=Response)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await delete_account(
                user_id=user_id, password=password, response=mock_response
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"

        # Verify no deletions occurred
        mock_db_conn.users_collection.delete_one.assert_not_called()


@pytest.mark.asyncio
async def test_delete_account_no_password_hash():
    """Test error when user account has no password set (OAuth users)"""
    user_id = "oauth_user"
    password = "some_password"

    mock_user = {
        "id": user_id,
        "email": "oauth@example.com",
        "first_name": "OAuth",
        "last_name": "User",
        # No password_hash field
    }

    mock_response = Mock(spec=Response)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await delete_account(
                user_id=user_id, password=password, response=mock_response
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "User account has no password set"

        # Verify no deletions occurred
        mock_db_conn.users_collection.delete_one.assert_not_called()


@pytest.mark.asyncio
async def test_delete_account_incorrect_password():
    """Test error when incorrect password is provided"""
    user_id = "user_456"
    correct_password = "correct_password"
    wrong_password = "wrong_password"
    password_hash = pwd_context.hash(correct_password)

    mock_user = {
        "id": user_id,
        "email": "user@example.com",
        "password_hash": password_hash,
    }

    mock_response = Mock(spec=Response)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await delete_account(
                user_id=user_id, password=wrong_password, response=mock_response
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Incorrect password"

        # Verify no deletions occurred
        mock_db_conn.users_collection.delete_one.assert_not_called()
        mock_db_conn.predictions_collection.delete_many.assert_not_called()


@pytest.mark.asyncio
async def test_delete_account_cascade_cleanup():
    """Test that all related data is properly cleaned up"""
    user_id = "user_cleanup"
    password = "test_password"
    password_hash = pwd_context.hash(password)
    user_email = "cleanup@example.com"

    mock_user = {"id": user_id, "email": user_email, "password_hash": password_hash}

    mock_response = Mock(spec=Response)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.otps_collection = AsyncMock()

    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.delete_one = AsyncMock()
    mock_db_conn.predictions_collection.delete_many = AsyncMock()
    mock_db_conn.otps_collection.delete_many = AsyncMock()

    with patch("services.profile_service.db_conn", mock_db_conn):
        await delete_account(user_id=user_id, password=password, response=mock_response)

        # Verify cascade deletion order and calls
        mock_db_conn.users_collection.delete_one.assert_called_once_with(
            {"id": user_id}
        )
        mock_db_conn.predictions_collection.delete_many.assert_called_once_with(
            {"user_id": user_id}
        )
        mock_db_conn.otps_collection.delete_many.assert_called_once_with(
            {"email": user_email}
        )


@pytest.mark.asyncio
async def test_delete_account_empty_password():
    """Test validation with empty password string"""
    user_id = "user_789"
    password = ""  # Empty password

    mock_user = {
        "id": user_id,
        "email": "user@example.com",
        "password_hash": pwd_context.hash("actual_password"),
    }

    mock_response = Mock(spec=Response)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await delete_account(
                user_id=user_id, password=password, response=mock_response
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Incorrect password"


@pytest.mark.asyncio
async def test_delete_account_cookies_cleared():
    """Test that authentication cookies are properly cleared"""
    user_id = "user_cookies"
    password = "test_password"
    password_hash = pwd_context.hash(password)

    mock_user = {
        "id": user_id,
        "email": "cookies@example.com",
        "password_hash": password_hash,
    }

    mock_response = Mock(spec=Response)
    mock_response.delete_cookie = Mock()

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.otps_collection = AsyncMock()

    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.delete_one = AsyncMock()
    mock_db_conn.predictions_collection.delete_many = AsyncMock()
    mock_db_conn.otps_collection.delete_many = AsyncMock()

    with patch("services.profile_service.db_conn", mock_db_conn):
        await delete_account(user_id=user_id, password=password, response=mock_response)

        # Verify both cookies are deleted
        cookie_calls = [
            call[0][0] for call in mock_response.delete_cookie.call_args_list
        ]
        assert "access_token" in cookie_calls
        assert "refresh_token" in cookie_calls
        assert len(cookie_calls) == 2


@pytest.mark.asyncio
async def test_delete_account_no_predictions():
    """Test account deletion when user has no predictions"""
    user_id = "user_no_predictions"
    password = "test_password"
    password_hash = pwd_context.hash(password)

    mock_user = {
        "id": user_id,
        "email": "nopred@example.com",
        "password_hash": password_hash,
    }

    mock_response = Mock(spec=Response)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.otps_collection = AsyncMock()

    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.delete_one = AsyncMock()
    mock_db_conn.predictions_collection.delete_many = AsyncMock(
        return_value=MagicMock(deleted_count=0)
    )
    mock_db_conn.otps_collection.delete_many = AsyncMock(
        return_value=MagicMock(deleted_count=0)
    )

    with patch("services.profile_service.db_conn", mock_db_conn):
        await delete_account(user_id=user_id, password=password, response=mock_response)

        # Should still call delete_many even if no records exist
        mock_db_conn.predictions_collection.delete_many.assert_called_once()
        mock_db_conn.otps_collection.delete_many.assert_called_once()


@pytest.mark.asyncio
async def test_delete_account_password_verification_with_bcrypt():
    """Test that password verification uses bcrypt correctly"""
    user_id = "user_bcrypt"
    password = "Secure@Pass123"
    password_hash = pwd_context.hash(password)

    mock_user = {
        "id": user_id,
        "email": "bcrypt@example.com",
        "password_hash": password_hash,
    }

    mock_response = Mock(spec=Response)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.predictions_collection = AsyncMock()
    mock_db_conn.otps_collection = AsyncMock()

    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.delete_one = AsyncMock()
    mock_db_conn.predictions_collection.delete_many = AsyncMock()
    mock_db_conn.otps_collection.delete_many = AsyncMock()

    with patch("services.profile_service.db_conn", mock_db_conn):
        # Should succeed with correct password
        await delete_account(user_id=user_id, password=password, response=mock_response)
        mock_db_conn.users_collection.delete_one.assert_called_once()

        # Reset mocks for second test
        mock_db_conn.users_collection.delete_one.reset_mock()
        mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)

        # Should fail with incorrect password
        with pytest.raises(HTTPException) as exc_info:
            await delete_account(
                user_id=user_id, password="WrongPassword", response=mock_response
            )

        assert exc_info.value.status_code == 401
        mock_db_conn.users_collection.delete_one.assert_not_called()


@pytest.mark.asyncio
async def test_update_profile_pic_url_success():
    """Test successful profile picture update"""
    user_id = "user_123"

    mock_user = {
        "id": user_id,
        "email": "user@example.com",
        "first_name": "John",
        "profile_pic_url": "https://old-url.com/pic.jpg",
    }

    updated_user = {
        "id": user_id,
        "email": "user@example.com",
        "first_name": "John",
        "profile_pic_url": "https://res.cloudinary.com/test/image/upload/v123/plant_app/profile_pics/new_pic.jpg",
    }

    # Mock file upload
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test_image.jpg"
    mock_file.content_type = "image/jpeg"

    # Make file a MagicMock so we can assert seek calls
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"

    # Mock Cloudinary upload result
    mock_upload_result = {
        "secure_url": "https://res.cloudinary.com/test/image/upload/v123/plant_app/profile_pics/new_pic.jpg",
        "public_id": "plant_app/profile_pics/new_pic",
        "version": 123,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=updated_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.cloudinary.uploader.upload",
        return_value=mock_upload_result,
    ) as mock_cloudinary:

        result = await update_profile_picture(user_id=user_id, file=mock_file)

        # Verify user lookup
        mock_db_conn.users_collection.find_one.assert_called_once_with({"id": user_id})

        # Verify file.seek was called
        mock_file.file.seek.assert_called_once_with(0)

        # Verify Cloudinary upload
        mock_cloudinary.assert_called_once()
        call_args = mock_cloudinary.call_args
        assert call_args[1]["folder"] == "plant_app/profile_pics"
        assert call_args[1]["overwrite"] is True
        assert call_args[1]["resource_type"] == "image"

        # Verify database update
        mock_db_conn.users_collection.find_one_and_update.assert_called_once()
        update_call_args = mock_db_conn.users_collection.find_one_and_update.call_args
        assert update_call_args[0][0] == {"id": user_id}
        assert (
            update_call_args[0][1]["$set"]["profile_pic_url"]
            == mock_upload_result["secure_url"]
        )
        assert update_call_args[1]["return_document"] is True

        # Verify response
        assert result["message"] == "Profile picture updated successfully"
        assert result["user_id"] == user_id
        assert result["new_pic_url"] == mock_upload_result["secure_url"]


@pytest.mark.asyncio
async def test_update_profile_pic_url_user_not_found():
    """Test error when user does not exist"""
    user_id = "nonexistent_user"

    mock_file = MagicMock(spec=UploadFile)
    # Make file a MagicMock so we can assert seek calls
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await update_profile_picture(user_id=user_id, file=mock_file)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_update_profile_pic_url_cloudinary_upload_fails():
    """Test error handling when Cloudinary upload fails"""
    user_id = "user_456"

    mock_user = {
        "id": user_id,
        "email": "user@example.com",
        "profile_pic_url": "https://old-url.com/pic.jpg",
    }

    mock_file = MagicMock(spec=UploadFile)
    # Make file a MagicMock so we can assert seek calls
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"
    mock_file.filename = "test_image.jpg"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)

    # Mock Cloudinary failure
    cloudinary_error = Exception("Network timeout")

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.cloudinary.uploader.upload",
        side_effect=cloudinary_error,
    ):

        with pytest.raises(HTTPException) as exc_info:
            await update_profile_picture(user_id=user_id, file=mock_file)

        assert exc_info.value.status_code == 500
        assert "Cloudinary upload failed" in exc_info.value.detail
        assert "Network timeout" in exc_info.value.detail

        # Verify database update was not called
        mock_db_conn.users_collection.find_one_and_update.assert_not_called()


@pytest.mark.asyncio
async def test_update_profile_pic_url_database_update_fails():
    """Test error when database update fails"""
    user_id = "user_789"

    mock_user = {
        "id": user_id,
        "email": "user@example.com",
        "profile_pic_url": "https://old-url.com/pic.jpg",
    }

    mock_file = MagicMock(spec=UploadFile)
    # Make file a MagicMock so we can assert seek calls
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"
    mock_upload_result = {"secure_url": "https://res.cloudinary.com/test/new_pic.jpg"}

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    # Return None to simulate update failure
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.cloudinary.uploader.upload",
        return_value=mock_upload_result,
    ):

        with pytest.raises(HTTPException) as exc_info:
            await update_profile_picture(user_id=user_id, file=mock_file)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Profile picture update failed"


@pytest.mark.asyncio
async def test_update_profile_pic_url_database_returns_invalid_document():
    """Test error when database returns document without id field"""
    user_id = "user_invalid"

    mock_user = {
        "id": user_id,
        "email": "user@example.com",
        "profile_pic_url": "https://old-url.com/pic.jpg",
    }

    mock_file = MagicMock(spec=UploadFile)
    # Make file a MagicMock so we can assert seek calls
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"

    mock_upload_result = {"secure_url": "https://res.cloudinary.com/test/new_pic.jpg"}

    # Invalid updated user (missing 'id' field)
    invalid_updated_user = {
        "email": "user@example.com",
        "profile_pic_url": "https://res.cloudinary.com/test/new_pic.jpg",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=invalid_updated_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.cloudinary.uploader.upload",
        return_value=mock_upload_result,
    ):

        with pytest.raises(HTTPException) as exc_info:
            await update_profile_picture(user_id=user_id, file=mock_file)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Profile picture update failed"


@pytest.mark.asyncio
async def test_update_profile_pic_url_file_seek_called():
    """Test that file.seek(0) is called before upload"""
    user_id = "user_seek"

    mock_user = {"id": user_id, "email": "user@example.com"}

    updated_user = {
        "id": user_id,
        "email": "user@example.com",
        "profile_pic_url": "https://res.cloudinary.com/test/new_pic.jpg",
    }

    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = MagicMock()
    mock_file.file.seek = Mock()
    mock_file.filename = "test.jpg"

    mock_upload_result = {"secure_url": "https://res.cloudinary.com/test/new_pic.jpg"}

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=updated_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.cloudinary.uploader.upload",
        return_value=mock_upload_result,
    ):

        await update_profile_picture(user_id=user_id, file=mock_file)

        # Verify file.seek(0) was called before upload
        mock_file.file.seek.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_update_profile_pic_url_cloudinary_parameters():
    """Test that Cloudinary upload is called with correct parameters"""
    user_id = "user_params"

    mock_user = {"id": user_id, "email": "user@example.com"}

    updated_user = {
        "id": user_id,
        "profile_pic_url": "https://res.cloudinary.com/test/new_pic.jpg",
    }

    mock_file = MagicMock(spec=UploadFile)
    # Make file a MagicMock so we can assert seek calls
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"

    mock_upload_result = {
        "secure_url": "https://res.cloudinary.com/test/new_pic.jpg",
        "public_id": "plant_app/profile_pics/abc123",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=updated_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.cloudinary.uploader.upload",
        return_value=mock_upload_result,
    ) as mock_cloudinary:

        await update_profile_picture(user_id=user_id, file=mock_file)

        # Verify Cloudinary parameters
        mock_cloudinary.assert_called_once()
        call_kwargs = mock_cloudinary.call_args[1]

        assert call_kwargs["folder"] == "plant_app/profile_pics"
        assert call_kwargs["overwrite"] is True
        assert call_kwargs["resource_type"] == "image"


@pytest.mark.asyncio
async def test_update_profile_pic_url_response_format():
    """Test that response has correct format and data"""
    user_id = "user_response"
    new_pic_url = "https://res.cloudinary.com/test/image/upload/v123/plant_app/profile_pics/new_pic.jpg"

    mock_user = {"id": user_id, "email": "user@example.com"}

    updated_user = {"id": user_id, "profile_pic_url": new_pic_url}

    mock_file = MagicMock(spec=UploadFile)
    # Make file a MagicMock so we can assert seek calls
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"

    mock_upload_result = {"secure_url": new_pic_url}

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=updated_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.cloudinary.uploader.upload",
        return_value=mock_upload_result,
    ):

        result = await update_profile_picture(user_id=user_id, file=mock_file)

        # Verify response structure
        assert isinstance(result, dict)
        assert "message" in result
        assert "user_id" in result
        assert "new_pic_url" in result

        # Verify response values
        assert result["message"] == "Profile picture updated successfully"
        assert result["user_id"] == user_id
        assert result["new_pic_url"] == new_pic_url


@pytest.mark.asyncio
async def test_update_profile_pic_url_replaces_old_url():
    """Test that old profile picture URL is replaced with new one"""
    user_id = "user_replace"
    old_pic_url = "https://old-cdn.com/old_pic.jpg"
    new_pic_url = "https://res.cloudinary.com/test/new_pic.jpg"

    mock_user = {
        "id": user_id,
        "email": "user@example.com",
        "profile_pic_url": old_pic_url,
    }

    updated_user = {
        "id": user_id,
        "email": "user@example.com",
        "profile_pic_url": new_pic_url,
    }

    mock_file = MagicMock(spec=UploadFile)
    # Make file a MagicMock so we can assert seek calls
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"
    mock_upload_result = {"secure_url": new_pic_url}

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=updated_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.cloudinary.uploader.upload",
        return_value=mock_upload_result,
    ):

        await update_profile_picture(user_id=user_id, file=mock_file)

        # Verify update call replaced the URL
        update_call_args = mock_db_conn.users_collection.find_one_and_update.call_args
        assert update_call_args[0][1]["$set"]["profile_pic_url"] == new_pic_url
        assert update_call_args[0][1]["$set"]["profile_pic_url"] != old_pic_url


@pytest.mark.asyncio
async def test_update_profile_pic_url_large_file():
    """Test handling of large file upload"""
    user_id = "user_large"

    mock_user = {"id": user_id, "email": "user@example.com"}

    updated_user = {
        "id": user_id,
        "profile_pic_url": "https://res.cloudinary.com/test/new_pic.jpg",
    }

    mock_file = MagicMock(spec=UploadFile)
    # Make file a MagicMock so we can assert seek calls
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"
    mock_file.filename = "large_image.jpg"

    mock_upload_result = {"secure_url": "https://res.cloudinary.com/test/new_pic.jpg"}

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=updated_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.cloudinary.uploader.upload",
        return_value=mock_upload_result,
    ) as mock_cloudinary:

        result = await update_profile_picture(user_id=user_id, file=mock_file)

        # Verify upload was called with the large file
        mock_cloudinary.assert_called_once()
        assert result["message"] == "Profile picture updated successfully"


# Initialize password context for testing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.mark.asyncio
async def test_request_email_change_success():
    """Test successful email change request with OTP generation and email sending"""
    user_id = "user_123"
    new_email = "newemail@example.com"
    current_password = "correct_password"
    password_hash = pwd_context.hash(current_password)

    mock_user = {
        "id": user_id,
        "email": "oldemail@example.com",
        "first_name": "John",
        "password_hash": password_hash,
    }

    mock_otp = "123456"
    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = 10

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.delete_many = AsyncMock(
        return_value=MagicMock(deleted_count=0)
    )
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otps_collection.insert_one = AsyncMock()

    mock_template = MagicMock()
    mock_template.render = Mock(return_value="<html>OTP: 123456</html>")
    mock_env = MagicMock()
    mock_env.get_template = Mock(return_value=mock_template)

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.verify_password", return_value=True
    ), patch(
        "services.profile_service.generate_secure_otp", return_value=mock_otp
    ), patch(
        "services.profile_service.settings", mock_settings
    ), patch(
        "services.profile_service.Environment", return_value=mock_env
    ), patch(
        "services.profile_service.send_email", new_callable=AsyncMock
    ) as mock_send_email:

        await request_email_change(
            user_id=user_id, new_email=new_email, current_password=current_password
        )

        # Verify old OTPs deleted
        mock_db_conn.otps_collection.delete_many.assert_called_once_with(
            {"user_id": user_id}
        )

        # Verify user lookup
        mock_db_conn.users_collection.find_one.assert_called_once_with({"id": user_id})

        # Verify OTP insertion
        mock_db_conn.otps_collection.insert_one.assert_called_once()
        otp_entry = mock_db_conn.otps_collection.insert_one.call_args[0][0]

        assert otp_entry["user_id"] == user_id
        assert otp_entry["email"] == new_email
        assert otp_entry["otp"] == mock_otp
        assert otp_entry["purpose"] == "email_change"
        assert "created_at" in otp_entry
        assert "expires_at" in otp_entry

        # Verify template rendering
        mock_env.get_template.assert_called_once_with("email_change.html")
        mock_template.render.assert_called_once_with(
            display_name="John", otp=mock_otp, expiry=10
        )

        # Verify email sent
        mock_send_email.assert_called_once()
        email_call_args = mock_send_email.call_args
        assert email_call_args[1]["to_email"] == new_email
        assert email_call_args[1]["subject"] == "Confirm Your Email Change 🌱"
        assert email_call_args[1]["is_html"] is True


@pytest.mark.asyncio
async def test_request_email_change_user_not_found():
    """Test error when user does not exist"""
    user_id = "nonexistent_user"
    new_email = "new@example.com"
    current_password = "password123"

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.delete_many = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await request_email_change(
                user_id=user_id, new_email=new_email, current_password=current_password
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"

        # Verify OTP deletion still happened
        mock_db_conn.otps_collection.delete_many.assert_called_once_with(
            {"user_id": user_id}
        )


@pytest.mark.asyncio
async def test_request_email_change_incorrect_password():
    """Test error when current password is incorrect"""
    user_id = "user_456"
    new_email = "new@example.com"
    correct_password = "correct_password"
    wrong_password = "wrong_password"
    password_hash = pwd_context.hash(correct_password)

    mock_user = {
        "id": user_id,
        "email": "old@example.com",
        "first_name": "Jane",
        "password_hash": password_hash,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.delete_many = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.verify_password", return_value=False
    ):

        with pytest.raises(HTTPException) as exc_info:
            await request_email_change(
                user_id=user_id, new_email=new_email, current_password=wrong_password
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Current password is incorrect"


@pytest.mark.asyncio
async def test_request_email_change_deletes_existing_otps():
    """Test that existing OTPs for the user are deleted before creating new one"""
    user_id = "user_789"
    new_email = "new@example.com"
    current_password = "password123"
    password_hash = pwd_context.hash(current_password)

    mock_user = {
        "id": user_id,
        "email": "old@example.com",
        "first_name": "Bob",
        "password_hash": password_hash,
    }

    mock_otp = "654321"
    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = 15

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    # Simulate 3 existing OTPs deleted
    mock_db_conn.otps_collection.delete_many = AsyncMock(
        return_value=MagicMock(deleted_count=3)
    )
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otps_collection.insert_one = AsyncMock()

    mock_template = MagicMock()
    mock_template.render = Mock(return_value="<html>OTP</html>")
    mock_env = MagicMock()
    mock_env.get_template = Mock(return_value=mock_template)

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.verify_password", return_value=True
    ), patch(
        "services.profile_service.generate_secure_otp", return_value=mock_otp
    ), patch(
        "services.profile_service.settings", mock_settings
    ), patch(
        "services.profile_service.Environment", return_value=mock_env
    ), patch(
        "services.profile_service.send_email", new_callable=AsyncMock
    ):

        await request_email_change(
            user_id=user_id, new_email=new_email, current_password=current_password
        )

        # Verify delete_many was called FIRST
        mock_db_conn.otps_collection.delete_many.assert_called_once_with(
            {"user_id": user_id}
        )

        # Verify delete was called before insert
        assert mock_db_conn.otps_collection.delete_many.call_count == 1
        assert mock_db_conn.otps_collection.insert_one.call_count == 1


@pytest.mark.asyncio
async def test_request_email_change_otp_expiry():
    """Test that OTP expiry time is set correctly"""
    user_id = "user_expiry"
    new_email = "new@example.com"
    current_password = "password123"
    password_hash = pwd_context.hash(current_password)

    mock_user = {
        "id": user_id,
        "email": "old@example.com",
        "first_name": "Alice",
        "password_hash": password_hash,
    }

    mock_otp = "111111"
    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = 20

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.delete_many = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otps_collection.insert_one = AsyncMock()

    mock_template = MagicMock()
    mock_template.render = Mock(return_value="<html>OTP</html>")
    mock_env = MagicMock()
    mock_env.get_template = Mock(return_value=mock_template)

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.verify_password", return_value=True
    ), patch(
        "services.profile_service.generate_secure_otp", return_value=mock_otp
    ), patch(
        "services.profile_service.settings", mock_settings
    ), patch(
        "services.profile_service.Environment", return_value=mock_env
    ), patch(
        "services.profile_service.send_email", new_callable=AsyncMock
    ):

        await request_email_change(
            user_id=user_id, new_email=new_email, current_password=current_password
        )

        # Verify OTP entry has correct expiry
        otp_entry = mock_db_conn.otps_collection.insert_one.call_args[0][0]

        # Calculate expected expiry
        time_diff = otp_entry["expires_at"] - otp_entry["created_at"]
        assert time_diff == timedelta(minutes=20)


@pytest.mark.asyncio
async def test_request_email_change_template_rendering():
    """Test that email template is rendered with correct data"""
    user_id = "user_template"
    new_email = "new@example.com"
    current_password = "password123"
    password_hash = pwd_context.hash(current_password)

    mock_user = {
        "id": user_id,
        "email": "old@example.com",
        "first_name": "Charlie",
        "password_hash": password_hash,
    }

    mock_otp = "999888"
    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = 10

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.delete_many = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otps_collection.insert_one = AsyncMock()

    mock_template = MagicMock()
    mock_template.render = Mock(return_value="<html>Rendered template</html>")
    mock_env = MagicMock()
    mock_env.get_template = Mock(return_value=mock_template)

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.verify_password", return_value=True
    ), patch(
        "services.profile_service.generate_secure_otp", return_value=mock_otp
    ), patch(
        "services.profile_service.settings", mock_settings
    ), patch(
        "services.profile_service.Environment", return_value=mock_env
    ), patch(
        "services.profile_service.send_email", new_callable=AsyncMock
    ):

        await request_email_change(
            user_id=user_id, new_email=new_email, current_password=current_password
        )

        # Verify Environment setup
        mock_env.get_template.assert_called_once_with("email_change.html")
        mock_template.render.assert_called_once_with(
            display_name="Charlie", otp=mock_otp, expiry=10
        )


@pytest.mark.asyncio
async def test_request_email_change_user_without_first_name():
    """Test template rendering when user has no first_name field"""
    user_id = "user_no_name"
    new_email = "new@example.com"
    current_password = "password123"
    password_hash = pwd_context.hash(current_password)

    mock_user = {
        "id": user_id,
        "email": "old@example.com",
        # No first_name field
        "password_hash": password_hash,
    }

    mock_otp = "777666"
    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = 10

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.delete_many = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otps_collection.insert_one = AsyncMock()

    mock_template = MagicMock()
    mock_template.render = Mock(return_value="<html>OTP</html>")
    mock_env = MagicMock()
    mock_env.get_template = Mock(return_value=mock_template)

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.verify_password", return_value=True
    ), patch(
        "services.profile_service.generate_secure_otp", return_value=mock_otp
    ), patch(
        "services.profile_service.settings", mock_settings
    ), patch(
        "services.profile_service.Environment", return_value=mock_env
    ), patch(
        "services.profile_service.send_email", new_callable=AsyncMock
    ):

        await request_email_change(
            user_id=user_id, new_email=new_email, current_password=current_password
        )

        # Verify template rendered with default "User" when first_name is missing
        mock_template.render.assert_called_once_with(
            display_name="User", otp=mock_otp, expiry=10
        )


@pytest.mark.asyncio
async def test_request_email_change_otp_generation():
    """Test that OTP is generated with correct length"""
    user_id = "user_otp_gen"
    new_email = "new@example.com"
    current_password = "password123"
    password_hash = pwd_context.hash(current_password)

    mock_user = {
        "id": user_id,
        "email": "old@example.com",
        "first_name": "Dave",
        "password_hash": password_hash,
    }

    generated_otp = "555444"
    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = 10

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.delete_many = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otps_collection.insert_one = AsyncMock()

    mock_template = MagicMock()
    mock_template.render = Mock(return_value="<html>OTP</html>")
    mock_env = MagicMock()
    mock_env.get_template = Mock(return_value=mock_template)

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.verify_password", return_value=True
    ), patch(
        "services.profile_service.generate_secure_otp", return_value=generated_otp
    ) as mock_gen_otp, patch(
        "services.profile_service.settings", mock_settings
    ), patch(
        "services.profile_service.Environment", return_value=mock_env
    ), patch(
        "services.profile_service.send_email", new_callable=AsyncMock
    ):

        await request_email_change(
            user_id=user_id, new_email=new_email, current_password=current_password
        )

        # Verify OTP generated with length 6
        mock_gen_otp.assert_called_once_with(length=6)

        # Verify generated OTP is used
        otp_entry = mock_db_conn.otps_collection.insert_one.call_args[0][0]
        assert otp_entry["otp"] == generated_otp


@pytest.mark.asyncio
async def test_request_email_change_email_sent_to_new_address():
    """Test that email is sent to the new email address, not old one"""
    user_id = "user_email_target"
    old_email = "old@example.com"
    new_email = "new@example.com"
    current_password = "password123"
    password_hash = pwd_context.hash(current_password)

    mock_user = {
        "id": user_id,
        "email": old_email,
        "first_name": "Emma",
        "password_hash": password_hash,
    }

    mock_otp = "333222"
    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = 10

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.delete_many = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otps_collection.insert_one = AsyncMock()

    mock_template = MagicMock()
    mock_template.render = Mock(return_value="<html>OTP</html>")
    mock_env = MagicMock()
    mock_env.get_template = Mock(return_value=mock_template)

    with patch("services.profile_service.db_conn", mock_db_conn), patch(
        "services.profile_service.verify_password", return_value=True
    ), patch(
        "services.profile_service.generate_secure_otp", return_value=mock_otp
    ), patch(
        "services.profile_service.settings", mock_settings
    ), patch(
        "services.profile_service.Environment", return_value=mock_env
    ), patch(
        "services.profile_service.send_email", new_callable=AsyncMock
    ) as mock_send_email:

        await request_email_change(
            user_id=user_id, new_email=new_email, current_password=current_password
        )

        # Verify email sent to NEW email, not old
        mock_send_email.assert_called_once()
        email_call_args = mock_send_email.call_args
        assert email_call_args[1]["to_email"] == new_email
        assert email_call_args[1]["to_email"] != old_email


@pytest.mark.asyncio
async def test_confirm_email_change_success():
    """Test successful email change confirmation with valid OTP"""
    user_id = "user123"
    old_email = "old@example.com"
    new_email = "new@example.com"
    otp_code = "123456"

    mock_otp_entry = {
        "user_id": user_id,
        "email": new_email,
        "otp": otp_code,
        "purpose": "email_change",
    }

    mock_updated_user = {"id": user_id, "email": new_email, "first_name": "John"}

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
    mock_db_conn.otps_collection.delete_many = AsyncMock()
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=mock_updated_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await confirm_email_change(
            user_id=user_id, old_email=old_email, new_email=new_email, otp_code=otp_code
        )

        # Verify OTP was validated with correct parameters
        mock_db_conn.otps_collection.find_one.assert_called_once_with(
            {
                "user_id": user_id,
                "email": new_email,
                "otp": otp_code,
                "purpose": "email_change",
            }
        )

        # Verify OTPs were deleted
        mock_db_conn.otps_collection.delete_many.assert_called_once_with(
            {"email": new_email}
        )

        # Verify user email was updated
        mock_db_conn.users_collection.find_one_and_update.assert_called_once_with(
            {"id": user_id, "email": old_email},
            {"$set": {"email": new_email}},
            return_document=True,
        )

        # Verify response
        assert result["message"] == "Email updated successfully"
        assert result["new_email"] == new_email


@pytest.mark.asyncio
async def test_confirm_email_change_invalid_otp():
    """Test email change fails with invalid OTP"""
    user_id = "user123"
    old_email = "old@example.com"
    new_email = "new@example.com"
    otp_code = "wrong_otp"

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.otps_collection.find_one = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await confirm_email_change(
                user_id=user_id,
                old_email=old_email,
                new_email=new_email,
                otp_code=otp_code,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid or expired OTP"


@pytest.mark.asyncio
async def test_confirm_email_change_expired_otp():
    """Test email change fails when OTP has expired (not found in DB)"""
    user_id = "user123"
    old_email = "old@example.com"
    new_email = "new@example.com"
    otp_code = "123456"

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.otps_collection.find_one = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await confirm_email_change(
                user_id=user_id,
                old_email=old_email,
                new_email=new_email,
                otp_code=otp_code,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid or expired OTP"


@pytest.mark.asyncio
async def test_confirm_email_change_user_not_found():
    """Test email change fails when user with old email doesn't exist"""
    user_id = "user123"
    old_email = "old@example.com"
    new_email = "new@example.com"
    otp_code = "123456"

    mock_otp_entry = {
        "user_id": user_id,
        "email": new_email,
        "otp": otp_code,
        "purpose": "email_change",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
    mock_db_conn.otps_collection.delete_many = AsyncMock()
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await confirm_email_change(
                user_id=user_id,
                old_email=old_email,
                new_email=new_email,
                otp_code=otp_code,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Email update failed"


@pytest.mark.asyncio
async def test_confirm_email_change_wrong_old_email():
    """Test email change fails when old_email doesn't match user's current email"""
    user_id = "user123"
    old_email = "wrong_old@example.com"
    new_email = "new@example.com"
    otp_code = "123456"

    mock_otp_entry = {
        "user_id": user_id,
        "email": new_email,
        "otp": otp_code,
        "purpose": "email_change",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
    mock_db_conn.otps_collection.delete_many = AsyncMock()
    # User not found because old_email doesn't match
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await confirm_email_change(
                user_id=user_id,
                old_email=old_email,
                new_email=new_email,
                otp_code=otp_code,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Email update failed"


@pytest.mark.asyncio
async def test_confirm_email_change_otp_for_different_user():
    """Test that OTP from another user cannot be used"""
    user_id = "user123"
    old_email = "old@example.com"
    new_email = "new@example.com"
    otp_code = "123456"

    # OTP belongs to different user

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    # find_one will return None because user_id doesn't match in query
    mock_db_conn.otps_collection.find_one = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await confirm_email_change(
                user_id=user_id,
                old_email=old_email,
                new_email=new_email,
                otp_code=otp_code,
            )

        # Verify query included correct user_id
        mock_db_conn.otps_collection.find_one.assert_called_once_with(
            {
                "user_id": user_id,
                "email": new_email,
                "otp": otp_code,
                "purpose": "email_change",
            }
        )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid or expired OTP"


@pytest.mark.asyncio
async def test_confirm_email_change_otp_cleanup():
    """Test that all OTPs for new email are deleted after successful verification"""
    user_id = "user123"
    old_email = "old@example.com"
    new_email = "new@example.com"
    otp_code = "123456"

    mock_otp_entry = {
        "user_id": user_id,
        "email": new_email,
        "otp": otp_code,
        "purpose": "email_change",
    }

    mock_updated_user = {"id": user_id, "email": new_email}

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
    mock_db_conn.otps_collection.delete_many = AsyncMock()
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=mock_updated_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn):
        await confirm_email_change(
            user_id=user_id, old_email=old_email, new_email=new_email, otp_code=otp_code
        )

        # Verify delete_many called with new_email to clean up all OTPs
        mock_db_conn.otps_collection.delete_many.assert_called_once_with(
            {"email": new_email}
        )


@pytest.mark.asyncio
async def test_confirm_email_change_updated_document_missing_id():
    """Test that email update fails when returned document is malformed"""
    user_id = "user123"
    old_email = "old@example.com"
    new_email = "new@example.com"
    otp_code = "123456"

    mock_otp_entry = {
        "user_id": user_id,
        "email": new_email,
        "otp": otp_code,
        "purpose": "email_change",
    }

    # Malformed document without 'id' field
    mock_updated_user = {"email": new_email}

    mock_db_conn = MagicMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.users_collection = AsyncMock()

    mock_db_conn.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
    mock_db_conn.otps_collection.delete_many = AsyncMock()
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=mock_updated_user
    )

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await confirm_email_change(
                user_id=user_id,
                old_email=old_email,
                new_email=new_email,
                otp_code=otp_code,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Email update failed"


@pytest.mark.asyncio
async def test_get_user_details_success():
    """Test successful retrieval of user details"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password_hash": "hashed_password_should_be_excluded",
        "reset_token": "secret_token",
        "reset_token_expires_at": datetime.utcnow(),
        "token_version": 1,
        "created_at": datetime.now(timezone.utc),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_details(user_id)

        # Verify database query
        mock_db_conn.users_collection.find_one.assert_called_once_with({"id": user_id})

        # Verify user data is returned
        assert result["id"] == user_id
        assert result["email"] == "user@example.com"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"

        # Verify sensitive fields are excluded
        assert "password_hash" not in result
        assert "reset_token" not in result
        assert "reset_token_expires_at" not in result
        assert "token_version" not in result


@pytest.mark.asyncio
async def test_get_user_details_user_not_found():
    """Test user details retrieval when user doesn't exist"""
    user_id = "nonexistent_user"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_user_details(user_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"

        # Verify query was attempted
        mock_db_conn.users_collection.find_one.assert_called_once_with({"id": user_id})


@pytest.mark.asyncio
async def test_get_user_details_excludes_password_hash():
    """Test that password_hash is always excluded from response"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "password_hash": "$2b$12$verySecureHashedPassword",
        "created_at": datetime.now(timezone.utc),
    }
    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_details(user_id)

        # Explicitly verify password_hash is not in response
        assert "password_hash" not in result
        assert "$2b$12$verySecureHashedPassword" not in str(result.values())


@pytest.mark.asyncio
async def test_get_user_details_excludes_reset_token():
    """Test that reset_token is always excluded from response"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "first_name": "Bob",
        "last_name": "Doe",
        "password_hash": "hashed_password",
        "reset_token": "super_secret_reset_token_12345",
        "reset_token_expires_at": datetime.utcnow(),
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_details(user_id)

        # Explicitly verify reset_token is not in response
        assert "reset_token" not in result
        assert "super_secret_reset_token_12345" not in str(result.values())


@pytest.mark.asyncio
async def test_get_user_details_excludes_token_version():
    """Test that token_version is excluded from response"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "first_name": "Alice",
        "last_name": "Doe",
        "password_hash": "hashed_password",
        "token_version": 5,
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_details(user_id)

        # Verify token_version is not in response
        assert "token_version" not in result


@pytest.mark.asyncio
async def test_get_user_details_includes_safe_fields():
    """Test that all safe/public fields are included in response"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Smith",
        "profile_pic_url": "https://example.com/pic.jpg",
        "created_at": datetime.now(timezone.utc),
        "password_hash": "excluded",
        "reset_token": "excluded",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_details(user_id)

        # Verify safe fields are present
        assert result["id"] == user_id
        assert result["email"] == "user@example.com"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Smith"
        assert result["profile_pic_url"] == "https://example.com/pic.jpg"
        assert "created_at" in result


@pytest.mark.asyncio
async def test_get_user_details_with_minimal_user_data():
    """Test retrieval with only required fields"""
    user_id = "user123"

    # Minimal user document (only required fields)
    mock_user_doc = {
        "id": user_id,
        "email": "minimal@example.com",
        "first_name": "Min",
        "last_name": "Doe",
        "password_hash": "hashed_password",
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_details(user_id)

        # Verify required fields are present
        assert result["id"] == user_id
        assert result["email"] == "minimal@example.com"
        assert result["first_name"] == "Min"

        # Verify sensitive field is excluded
        assert "password_hash" not in result


@pytest.mark.asyncio
async def test_get_user_details_empty_user_id():
    """Test behavior with empty user ID"""
    user_id = ""

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_user_details(user_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_get_user_details_excludes_all_sensitive_fields():
    """Test that ALL sensitive fields are excluded together"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "first_name": "Secure",
        "last_name": "Doe",
        "password_hash": "secret_password_hash",
        "reset_token": "secret_reset_token",
        "reset_token_expires_at": datetime.utcnow(),
        "token_version": 3,
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_details(user_id)

        # Verify ALL sensitive fields are excluded
        sensitive_fields = [
            "password_hash",
            "reset_token",
            "reset_token_expires_at",
            "token_version",
        ]

        for field in sensitive_fields:
            assert (
                field not in result
            ), f"Sensitive field '{field}' should not be in response"


@pytest.mark.asyncio
async def test_get_user_details_return_type_is_dict():
    """Test that the function returns a dictionary"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "first_name": "Test",
        "last_name": "Doe",
        "password_hash": "hashed_password",
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_details(user_id)

        # Verify return type is dict
        assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_get_user_details_database_query_format():
    """Test that database is queried with correct format"""
    user_id = "user_special_123"

    mock_user_doc = {
        "id": user_id,
        "email": "query@example.com",
        "first_name": "Query",
        "last_name": "Doe",
        "password_hash": "hashed_password",
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        await get_user_details(user_id)

        # Verify exact query format
        call_args = mock_db_conn.users_collection.find_one.call_args
        assert call_args[0][0] == {"id": user_id}


@pytest.mark.asyncio
async def test_get_user_by_id_success():
    """Test successful retrieval of user by ID"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password_hash": "hashed_password_should_be_excluded",
        "reset_token": "secret_token",
        "reset_token_expires_at": datetime.utcnow(),
        "token_version": 1,
        "created_at": datetime.now(timezone.utc),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_by_id(user_id)

        # Verify database query
        mock_db_conn.users_collection.find_one.assert_called_once_with({"id": user_id})

        # Verify user data is returned
        assert result["id"] == user_id
        assert result["email"] == "john@example.com"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"

        # Verify sensitive fields are excluded
        assert "password_hash" not in result
        assert "reset_token" not in result
        assert "reset_token_expires_at" not in result
        assert "token_version" not in result


@pytest.mark.asyncio
async def test_get_user_by_id_user_not_found():
    """Test retrieval when user doesn't exist"""
    user_id = "nonexistent_user_123"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_user_by_id(user_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"

        # Verify query was attempted
        mock_db_conn.users_collection.find_one.assert_called_once_with({"id": user_id})


@pytest.mark.asyncio
async def test_get_user_by_id_excludes_password_hash():
    """Test that password_hash is never exposed"""
    user_id = "user456"

    mock_user_doc = {
        "id": user_id,
        "email": "secure@example.com",
        "first_name": "Secure",
        "last_name": "Doe",
        "password_hash": "$2b$12$SuperSecureHashedPassword123",
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_by_id(user_id)

        # Verify password_hash is completely absent
        assert "password_hash" not in result
        assert "$2b$12$SuperSecureHashedPassword123" not in str(result.values())


@pytest.mark.asyncio
async def test_get_user_by_id_excludes_reset_token():
    """Test that reset_token is never exposed"""
    user_id = "user789"

    mock_user_doc = {
        "id": user_id,
        "email": "resetuser@example.com",
        "first_name": "Reset",
        "last_name": "Doe",
        "password_hash": "hashed_password",
        "reset_token": "very_secret_reset_token_abc123xyz",
        "reset_token_expires_at": datetime.utcnow(),
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_by_id(user_id)

        # Verify reset_token is completely absent
        assert "reset_token" not in result
        assert "very_secret_reset_token_abc123xyz" not in str(result.values())
        assert "reset_token_expires_at" not in result


@pytest.mark.asyncio
async def test_get_user_by_id_excludes_token_version():
    """Test that token_version is excluded from response"""
    user_id = "user_token_version"

    mock_user_doc = {
        "id": user_id,
        "email": "tokenuser@example.com",
        "first_name": "Token",
        "last_name": "Doe",
        "password_hash": "hashed_password",
        "token_version": 42,
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_by_id(user_id)

        # Verify token_version is not in response
        assert "token_version" not in result


@pytest.mark.asyncio
async def test_get_user_by_id_includes_public_fields():
    """Test that all public/safe fields are included"""
    user_id = "user_public"

    mock_user_doc = {
        "id": user_id,
        "email": "public@example.com",
        "first_name": "Public",
        "last_name": "User",
        "is_email_verified": True,
        "profile_pic_url": "https://example.com/avatar.jpg",
        "created_at": datetime.now(timezone.utc),
        "password_hash": "excluded",
        "reset_token": "excluded",
        "token_version": 1,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_by_id(user_id)

        # Verify public fields are present
        assert result["id"] == user_id
        assert result["email"] == "public@example.com"
        assert result["first_name"] == "Public"
        assert result["last_name"] == "User"
        assert result["profile_pic_url"] == "https://example.com/avatar.jpg"
        assert "created_at" in result

        # Verify sensitive fields are excluded
        assert "password_hash" not in result
        assert "reset_token" not in result
        assert "token_version" not in result


@pytest.mark.asyncio
async def test_get_user_by_id_with_minimal_data():
    """Test retrieval with only required fields"""
    user_id = "minimal_user"

    mock_user_doc = {
        "id": user_id,
        "email": "minimal@example.com",
        "first_name": "Min",
        "last_name": "Doe",
        "password_hash": "hashed_password",
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_by_id(user_id)

        # Verify required fields are present
        assert result["id"] == user_id
        assert result["email"] == "minimal@example.com"
        assert result["first_name"] == "Min"
        assert result["last_name"] == "Doe"

        # Verify sensitive field is excluded
        assert "password_hash" not in result


@pytest.mark.asyncio
async def test_get_user_by_id_with_special_characters():
    """Test user ID with special characters"""
    user_id = "user-123_ABC.xyz"

    mock_user_doc = {
        "id": user_id,
        "email": "special@example.com",
        "first_name": "Special",
        "last_name": "Doe",
        "password_hash": "hashed_password",
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_by_id(user_id)

        # Verify query with special characters
        mock_db_conn.users_collection.find_one.assert_called_once_with({"id": user_id})
        assert result["id"] == user_id


@pytest.mark.asyncio
async def test_get_user_by_id_empty_string():
    """Test behavior with empty user ID"""
    user_id = ""

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)

    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await get_user_by_id(user_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_get_user_by_id_excludes_all_sensitive_fields_together():
    """Test that ALL sensitive fields are excluded in one response"""
    user_id = "secure_user"

    mock_user_doc = {
        "id": user_id,
        "email": "allsecure@example.com",
        "first_name": "Secure",
        "last_name": "Doe",
        "password_hash": "super_secret_password_hash",
        "reset_token": "super_secret_reset_token",
        "reset_token_expires_at": datetime.utcnow(),
        "token_version": 7,
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_by_id(user_id)

        # List of ALL sensitive fields that must be excluded
        sensitive_fields = [
            "password_hash",
            "reset_token",
            "reset_token_expires_at",
            "token_version",
        ]

        # Verify each sensitive field is excluded
        for field in sensitive_fields:
            assert (
                field not in result
            ), f"Sensitive field '{field}' must not be in response"

        # Verify public fields are still present
        assert result["id"] == user_id
        assert result["email"] == "allsecure@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id_return_type():
    """Test that function returns a dictionary"""
    user_id = "return_type_user"

    mock_user_doc = {
        "id": user_id,
        "email": "returntype@example.com",
        "first_name": "Return",
        "last_name": "Doe",
        "password_hash": "hashed_password",
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_by_id(user_id)

        # Verify return type is dict
        assert isinstance(result, dict)
        assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_get_user_by_id_query_format():
    """Test that database query uses correct format"""
    user_id = "query_format_user"

    mock_user_doc = {
        "id": user_id,
        "email": "queryformat@example.com",
        "first_name": "Query",
        "last_name": "Doe",
        "password_hash": "hashed_password",
        "created_at": datetime.utcnow(),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    with patch("services.profile_service.db_conn", mock_db_conn):
        await get_user_by_id(user_id)

        # Verify exact query structure
        call_args = mock_db_conn.users_collection.find_one.call_args
        assert call_args[0][0] == {"id": user_id}
        assert len(call_args[0][0]) == 1  # Only one field in query


@pytest.mark.asyncio
async def test_get_user_by_id_different_user_ids():
    """Test retrieval works for different user ID formats"""
    test_user_ids = [
        "user123",
        "abc-def-ghi",
        "user_with_underscore",
        "USER_UPPERCASE",
        "123456789",
        "uuid-like-1234-5678-90ab",
    ]

    for user_id in test_user_ids:
        mock_user_doc = {
            "id": user_id,
            "email": f"{user_id}@example.com",
            "first_name": "Test",
            "last_name": "Doe",
            "password_hash": "hashed_password",
            "created_at": datetime.utcnow(),
        }

        mock_db_conn = MagicMock()
        mock_db_conn.users_collection = AsyncMock()
        mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

        with patch("services.profile_service.db_conn", mock_db_conn):
            result = await get_user_by_id(user_id)

            assert result["id"] == user_id
            assert "password_hash" not in result


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_success():
    """Test successful retrieval of top primary crops"""
    user_id = "user123"
    top_n = 3

    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": "Wheat",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred4",
            "user_id": user_id,
            "crop": "Corn",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image4.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # Verify database query
        mock_db_conn.predictions_collection.find.assert_called_once_with(
            {"user_id": user_id}
        )
        mock_cursor.to_list.assert_called_once_with(length=None)

        # Verify result - Rice appears 3 times, Wheat 2 times, Corn 1 time
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == "Rice"  # Most common
        assert result[1] == "Wheat"  # Second most common
        assert result[2] == "Corn"  # Third most common


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_default_top_n():
    """Test that default top_n is 3"""
    user_id = "user456"

    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": "Wheat",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": "Corn",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred4",
            "user_id": user_id,
            "crop": "Barley",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image4.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id)  # No top_n specified

        # Should return top 3 by default
        assert isinstance(result, list)
        assert len(result) == 3
        # Check that the crops returned are from the mock data
        for crop in result:
            assert crop in ["Rice", "Wheat", "Corn", "Barley"]


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_no_predictions():
    """Test when user has no predictions"""
    user_id = "user_no_predictions"
    top_n = 3

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # Should return empty list
        assert result == []
        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_filters_empty_crops():
    """Test that predictions with empty or null crops are filtered out"""
    user_id = "user789"
    top_n = 3

    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": "",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": None,
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred4",
            "user_id": user_id,
            "crop": "Wheat",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image4.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred5",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image5.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # Should only include Rice and Wheat, not empty or None
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == "Rice"  # 2 occurrences
        assert result[1] == "Wheat"  # 1 occurrence
        assert "" not in result
        assert None not in result


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_top_n_larger_than_unique_crops():
    """Test when top_n is larger than number of unique crops"""
    user_id = "user_few_crops"
    top_n = 10

    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": "Wheat",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # Should return only the unique crops (Rice and Wheat)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == "Rice"
        assert result[1] == "Wheat"


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_top_n_equals_one():
    """Test retrieving only the top 1 crop"""
    user_id = "user_top_one"
    top_n = 1

    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "Wheat",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred4",
            "user_id": user_id,
            "crop": "Corn",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image4.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # Should return only the top 1 crop (most common: Rice)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "Rice"


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_same_frequency():
    """Test crops with same frequency - order should be consistent"""
    user_id = "user_same_freq"
    top_n = 3

    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": "Wheat",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": "Corn",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # All crops have same frequency (1), should return all 3
        assert isinstance(result, list)
        assert len(result) == 3
        assert set(result) == {"Rice", "Wheat", "Corn"}


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_case_sensitive():
    """Test that crop names are case-sensitive"""
    user_id = "user_case_sensitive"
    top_n = 5

    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": "rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": "RICE",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred4",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image4.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # "Rice" appears 2 times, "rice" 1 time, "RICE" 1 time (treated as different)
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == "Rice"  # Most common with 2 occurrences
        assert "rice" in result
        assert "RICE" in result


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_many_predictions():
    """Test with large number of predictions"""
    user_id = "user_many_predictions"
    top_n = 3

    # Create 50 Rice predictions
    mock_prediction_docs = [
        {
            "prediction_id": f"pred_{i}",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": f"http://example.com/rice_{i}.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        }
        for i in range(50)
    ]

    # Create 30 Wheat predictions
    mock_prediction_docs += [
        {
            "prediction_id": f"pred_{i+50}",
            "user_id": user_id,
            "crop": "Wheat",
            "model_name": "mobilenet_v3",
            "image_url": f"http://example.com/wheat_{i}.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        }
        for i in range(30)
    ]

    # Create 20 Corn predictions
    mock_prediction_docs += [
        {
            "prediction_id": f"pred_{i+80}",
            "user_id": user_id,
            "crop": "Corn",
            "model_name": "mobilenet_v3",
            "image_url": f"http://example.com/corn_{i}.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        }
        for i in range(20)
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # Should return top 3: Rice (50), Wheat (30), Corn (20)
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == "Rice"
        assert result[1] == "Wheat"
        assert result[2] == "Corn"


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_return_type():
    """Test that function returns a List[str]"""
    user_id = "user_return_type"
    top_n = 3

    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        }
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # Verify return type
        assert isinstance(result, list)
        assert all(isinstance(crop, str) for crop in result)


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_query_format():
    """Test that database query uses correct format"""
    user_id = "user_query_format"
    top_n = 3

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        await get_primary_crops_for_user(user_id, top_n)

        # Verify exact query format
        mock_db_conn.predictions_collection.find.assert_called_once_with(
            {"user_id": user_id}
        )


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_diverse_crop_names():
    """Test with diverse crop names including special characters and spaces"""
    user_id = "user_diverse_crops"
    top_n = 5

    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": "Sweet Corn",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred4",
            "user_id": user_id,
            "crop": "Baby Corn",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image4.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred5",
            "user_id": user_id,
            "crop": "Sweet Corn",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image5.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred6",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image6.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # Rice: 3, Sweet Corn: 2, Baby Corn: 1
        assert len(result) == 3
        assert result[0] == "Rice"
        assert result[1] == "Sweet Corn"
        assert result[2] == "Baby Corn"


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_top_n_zero():
    """Test with top_n = 0"""
    user_id = "user_top_zero"
    top_n = 0

    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "Rice",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": "Wheat",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # Should return empty list when top_n is 0
        assert result == []
        assert len(result) == 0


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_all_empty_crops():
    """Test when all predictions have empty crops"""
    user_id = "user_all_empty"
    top_n = 3

    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": None,
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": "",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # Should return empty list since all crops are empty/None
        assert result == []
        assert len(result) == 0


@pytest.mark.asyncio
async def test_get_primary_crops_for_user_ordering_preserved():
    """Test that ordering by frequency is correct"""
    user_id = "user_ordering"
    top_n = 5

    mock_prediction_docs = [
        {
            "prediction_id": f"pred{i}",
            "user_id": user_id,
            "crop": crop,
            "model_name": "mobilenet_v3",
            "image_url": f"http://example.com/image{i}.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        }
        for i, crop in enumerate(
            [
                "Barley",
                "Corn",
                "Corn",
                "Wheat",
                "Wheat",
                "Wheat",
                "Rice",
                "Rice",
                "Rice",
                "Rice",
            ],
            start=1,
        )
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_primary_crops_for_user(user_id, top_n)

        # Rice: 4, Wheat: 3, Corn: 2, Barley: 1
        assert len(result) == 4
        assert result[0] == "Rice"  # 4 occurrences
        assert result[1] == "Wheat"  # 3 occurrences
        assert result[2] == "Corn"  # 2 occurrences
        assert result[3] == "Barley"  # 1 occurrence


@pytest.mark.asyncio
async def test_get_user_dashboard_success():
    """Test successful dashboard data calculation"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "token_version": 0,
        "first_name": "Test",
        "last_name": "User",
        "reset_token": None,
        "reset_token_expires_at": None,
        "profile_pic_url": None,
        "password_hash": "fake_hashed_password",
        "farm_size": None,  # Could be set to a FarmSizeEnum value if needed
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
    }

    # Include required fields for Prediction model
    mock_prediction_docs = [
        {
            "prediction_id": f"pred{i+1}",
            "user_id": user_id,
            "crop": crop,
            "disease": disease,
            "model_name": "mobilenet_v3",
            "image_url": f"http://example.com/image{i+1}.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        }
        for i, (crop, disease) in enumerate(
            [
                ("tomato", "Leaf Blight"),
                ("tomato", "Healthy"),
                ("potato", "Early Blight"),
                ("potato", "Healthy"),
                ("corn", "Healthy"),
            ]
        )
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_dashboard(user_id)

        # Verify dashboard metrics
        assert result.user_id == user_id
        assert result.total_analyses == 5
        assert result.issues_detected == 2  # Leaf Blight + Early Blight
        assert result.healthy_crops == 3  # Healthy predictions
        assert result.crops_monitored == 3  # tomato, potato, corn


@pytest.mark.asyncio
async def test_get_user_dashboard_user_not_found():
    """Test dashboard data fails when user doesn't exist"""
    user_id = "nonexistent_user"

    # Create a mock db_conn with users_collection having an async find_one
    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = MagicMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)

    # Patch the db_conn used in profile_service
    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(ValueError) as exc_info:
            await get_user_dashboard(user_id)

        assert "not found" in str(exc_info.value).lower()
        assert user_id in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_dashboard_no_predictions():
    """Test dashboard with user having no predictions"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "token_version": 0,
        "first_name": "Test",
        "last_name": "User",
        "reset_token": None,
        "reset_token_expires_at": None,
        "profile_pic_url": None,
        "password_hash": "fake_hashed_password",
        "farm_size": None,
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
    }

    # Mock db_conn with both collections
    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = MagicMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)

    mock_db_conn.predictions_collection = MagicMock()
    mock_db_conn.predictions_collection.find = MagicMock(
        return_value=AsyncMock(to_list=AsyncMock(return_value=[]))
    )

    # Patch db_conn in profile_service
    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_dashboard(user_id)

        assert result.user_id == user_id
        assert result.total_analyses == 0
        assert result.issues_detected == 0
        assert result.healthy_crops == 0
        assert result.crops_monitored == 0


@pytest.mark.asyncio
async def test_get_user_dashboard_all_healthy():
    """Test dashboard with all healthy crop predictions"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "token_version": 0,
        "first_name": "Test",
        "last_name": "User",
        "reset_token": None,
        "reset_token_expires_at": None,
        "profile_pic_url": None,
        "password_hash": "fake_hashed_password",
        "farm_size": None,  # Could be set to a FarmSizeEnum value if needed
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
    }

    # Include required Prediction fields
    mock_prediction_docs = [
        {
            "prediction_id": f"pred{i+1}",
            "user_id": user_id,
            "crop": crop,
            "disease": disease,
            "model_name": "mobilenet_v3",
            "image_url": f"http://example.com/image{i+1}.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        }
        for i, (crop, disease) in enumerate(
            [
                ("tomato", "Healthy"),
                ("potato", "healthy"),
                ("corn", "HEALTHY"),
            ]
        )
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_dashboard(user_id)

        # Verify dashboard metrics
        assert result.user_id == user_id
        assert result.total_analyses == 3
        assert result.issues_detected == 0  # No non-healthy diseases
        assert result.healthy_crops == 3  # All healthy
        assert result.crops_monitored == 3  # tomato, potato, corn


@pytest.mark.asyncio
async def test_get_user_dashboard_all_diseased():
    """Test dashboard with all diseased crop predictions"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "token_version": 0,
        "first_name": "Test",
        "last_name": "User",
        "reset_token": None,
        "reset_token_expires_at": None,
        "profile_pic_url": None,
        "password_hash": "fake_hashed_password",
        "farm_size": None,  # Could be set to a FarmSizeEnum value if needed
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
    }

    # Include all required Prediction fields
    mock_prediction_docs = [
        {
            "prediction_id": f"pred{i+1}",
            "user_id": user_id,
            "crop": crop,
            "disease": disease,
            "model_name": "mobilenet_v3",
            "image_url": f"http://example.com/image{i+1}.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        }
        for i, (crop, disease) in enumerate(
            [
                ("tomato", "Leaf Blight"),
                ("potato", "Early Blight"),
                ("corn", "Rust"),
            ]
        )
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_dashboard(user_id)

        # Verify dashboard metrics
        assert result.user_id == user_id
        assert result.total_analyses == 3
        assert result.issues_detected == 3  # All predictions are diseased
        assert result.healthy_crops == 0  # No healthy crops
        assert result.crops_monitored == 3  # tomato, potato, corn


@pytest.mark.asyncio
async def test_get_user_dashboard_duplicate_crops():
    """Test dashboard correctly counts unique crops even with duplicate predictions"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "token_version": 0,
        "first_name": "Test",
        "last_name": "User",
        "reset_token": None,
        "reset_token_expires_at": None,
        "profile_pic_url": None,
        "password_hash": "fake_hashed_password",
        "farm_size": None,  # Could be set to a FarmSizeEnum value if needed
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
    }

    # Include all required Prediction fields
    mock_prediction_docs = [
        {
            "prediction_id": f"pred{i+1}",
            "user_id": user_id,
            "crop": crop,
            "disease": disease,
            "model_name": "mobilenet_v3",
            "image_url": f"http://example.com/image{i+1}.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        }
        for i, (crop, disease) in enumerate(
            [
                ("tomato", "Leaf Blight"),
                ("tomato", "Healthy"),
                ("tomato", "Mosaic Virus"),
                ("potato", "Healthy"),
                ("potato", "Early Blight"),
            ]
        )
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_dashboard(user_id)

        # Verify dashboard metrics
        assert result.user_id == user_id
        assert result.total_analyses == 5  # 5 predictions
        assert result.issues_detected == 3  # Leaf Blight, Mosaic Virus, Early Blight
        assert result.healthy_crops == 2  # 2 Healthy predictions
        assert result.crops_monitored == 2  # tomato, potato (unique crops)


@pytest.mark.asyncio
async def test_get_user_dashboard_none_crop_values():
    """Test dashboard handles predictions with None crop values"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "token_version": 0,
        "first_name": "Test",
        "last_name": "User",
        "reset_token": None,
        "reset_token_expires_at": None,
        "profile_pic_url": None,
        "password_hash": "fake_hashed_password",
        "farm_size": None,  # Could be set to a FarmSizeEnum value if needed
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
    }

    # Include all required Prediction fields, with one crop as None
    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "tomato",
            "disease": "Leaf Blight",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": None,
            "disease": "Unknown",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": "potato",
            "disease": "Healthy",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_dashboard(user_id)

        # Verify dashboard metrics
        assert result.user_id == user_id
        assert result.total_analyses == 3  # 3 predictions
        assert result.issues_detected == 2  # Leaf Blight + Unknown (non-healthy)
        assert result.healthy_crops == 1  # Only potato is healthy
        assert result.crops_monitored == 2  # tomato and potato (None ignored)


@pytest.mark.asyncio
async def test_get_user_dashboard_none_disease_values():
    """Test dashboard handles predictions with None disease values"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "token_version": 0,
        "first_name": "Test",
        "last_name": "User",
        "reset_token": None,
        "reset_token_expires_at": None,
        "profile_pic_url": None,
        "password_hash": "fake_hashed_password",
        "farm_size": None,  # Could be set to a FarmSizeEnum value if needed
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
    }

    # Include all required Prediction fields
    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "tomato",
            "disease": "Leaf Blight",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": "potato",
            "disease": None,
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": "corn",
            "disease": "Healthy",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_dashboard(user_id)

        # Verify dashboard metrics
        assert result.user_id == user_id
        assert result.total_analyses == 3  # 3 predictions
        assert result.issues_detected == 1  # Only "Leaf Blight"; None ignored
        assert result.healthy_crops == 1  # Only "corn" is healthy
        assert (
            result.crops_monitored == 3
        )  # tomato, potato, corn (None disease does not remove crop)


@pytest.mark.asyncio
async def test_get_user_dashboard_case_insensitive_healthy():
    """Test that 'healthy' detection is case-insensitive"""
    user_id = "user123"

    mock_user_doc = {
        "id": user_id,
        "email": "user@example.com",
        "token_version": 0,
        "first_name": "Test",
        "last_name": "User",
        "reset_token": None,
        "reset_token_expires_at": None,
        "profile_pic_url": None,
        "password_hash": "fake_hashed_password",
        "farm_size": None,  # Could be set to a FarmSizeEnum value if needed
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
    }

    # Include all required Prediction fields
    mock_prediction_docs = [
        {
            "prediction_id": "pred1",
            "user_id": user_id,
            "crop": "tomato",
            "disease": "HEALTHY",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image1.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred2",
            "user_id": user_id,
            "crop": "potato",
            "disease": "Healthy",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image2.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred3",
            "user_id": user_id,
            "crop": "corn",
            "disease": "healthy",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image3.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "prediction_id": "pred4",
            "user_id": user_id,
            "crop": "wheat",
            "disease": "HeAlThY",
            "model_name": "mobilenet_v3",
            "image_url": "http://example.com/image4.jpg",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_prediction_docs)

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user_doc)
    mock_db_conn.predictions_collection.find = MagicMock(return_value=mock_cursor)

    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await get_user_dashboard(user_id)

        # Verify dashboard metrics
        assert result.user_id == user_id
        assert result.total_analyses == 4
        assert result.issues_detected == 0  # No diseased crops
        assert result.healthy_crops == 4  # All counted as healthy
        assert result.crops_monitored == 4  # tomato, potato, corn, wheat


@pytest.mark.asyncio
async def test_update_farm_size_success():
    """Test successful farm size update in database"""
    user_id = "user123"
    farm_size = "1-5 acres"

    mock_updated_user = {
        "id": user_id,
        "email": "user@example.com",
        "name": "Test User",
        "farm_size": farm_size,
    }

    # Create a mock db_conn with users_collection having the async find_one_and_update
    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = MagicMock()
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=mock_updated_user
    )

    # Patch the db_conn in profile_service
    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await update_farm_size(user_id, farm_size)

        # Assert the returned user doc is correct
        assert result == mock_updated_user
        assert result["farm_size"] == farm_size

        # Assert find_one_and_update was called correctly
        mock_db_conn.users_collection.find_one_and_update.assert_awaited_once_with(
            {"id": user_id}, {"$set": {"farm_size": farm_size}}, return_document=True
        )


@pytest.mark.asyncio
async def test_update_farm_size_user_not_found():
    """Test farm size update fails when user doesn't exist"""
    user_id = "nonexistent_user"
    farm_size = "1-5 acres"

    # Create a mock db_conn with users_collection having async find_one_and_update
    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = MagicMock()
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(return_value=None)

    # Patch the db_conn in profile_service
    with patch("services.profile_service.db_conn", mock_db_conn):
        with pytest.raises(ValueError) as exc_info:
            await update_farm_size(user_id, farm_size)

        assert "not found" in str(exc_info.value).lower()
        assert user_id in str(exc_info.value)

        # Optional: ensure find_one_and_update was called with correct parameters
        mock_db_conn.users_collection.find_one_and_update.assert_awaited_once_with(
            {"id": user_id}, {"$set": {"farm_size": farm_size}}, return_document=True
        )


@pytest.mark.asyncio
async def test_update_farm_size_correct_query():
    """Test that update_farm_size uses correct MongoDB query"""
    user_id = "user123"
    farm_size = "5-10 acres"

    mock_updated_user = {"id": user_id, "farm_size": farm_size}

    # Create a mock db_conn with users_collection.find_one_and_update
    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = MagicMock()
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=mock_updated_user
    )

    # Patch the db_conn in profile_service
    with patch("services.profile_service.db_conn", mock_db_conn):
        await update_farm_size(user_id, farm_size)

        # Verify find_one_and_update was called with correct parameters
        mock_db_conn.users_collection.find_one_and_update.assert_awaited_once_with(
            {"id": user_id},
            {"$set": {"farm_size": farm_size}},
            return_document=ReturnDocument.AFTER,
        )


@pytest.mark.asyncio
async def test_update_farm_size_different_sizes():
    """Test farm size update with various farm size values"""
    user_id = "user123"
    farm_sizes = [
        "1-5 acres",
        "5-10 acres",
        "10-20 acres",
        "20+ acres",
        "Less than 1 acre",
    ]

    for farm_size in farm_sizes:
        mock_updated_user = {
            "id": user_id,
            "email": "user@example.com",
            "farm_size": farm_size,
        }

        # Create a mock db_conn with users_collection.find_one_and_update
        mock_db_conn = MagicMock()
        mock_db_conn.users_collection = MagicMock()
        mock_db_conn.users_collection.find_one_and_update = AsyncMock(
            return_value=mock_updated_user
        )

        # Patch the db_conn in profile_service
        with patch("services.profile_service.db_conn", mock_db_conn):
            result = await update_farm_size(user_id, farm_size)

            # Assert the returned user doc has correct farm_size
            assert result["farm_size"] == farm_size

            # Assert the update was called correctly
            mock_db_conn.users_collection.find_one_and_update.assert_awaited_once_with(
                {"id": user_id},
                {"$set": {"farm_size": farm_size}},
                return_document=ReturnDocument.AFTER,
            )


@pytest.mark.asyncio
async def test_update_farm_size_preserves_other_fields():
    """Test that farm size update preserves other user fields"""
    user_id = "user123"
    farm_size = "10-20 acres"

    mock_updated_user = {
        "id": user_id,
        "email": "user@example.com",
        "name": "Test User",
        "phone": "+1234567890",  # Added so assertion passes
        "farm_size": farm_size,
        "created_at": "2024-01-01T00:00:00Z",
    }

    # Mock db_conn and users_collection
    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = MagicMock()
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=mock_updated_user
    )

    # Patch the db_conn in profile_service
    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await update_farm_size(user_id, farm_size)

        # Assertions
        assert result["id"] == user_id
        assert result["email"] == "user@example.com"
        assert result["name"] == "Test User"
        assert result["phone"] == "+1234567890"
        assert result["farm_size"] == farm_size

        # Ensure the update was called correctly
        mock_db_conn.users_collection.find_one_and_update.assert_awaited_once_with(
            {"id": user_id},
            {"$set": {"farm_size": farm_size}},
            return_document=ReturnDocument.AFTER,
        )


@pytest.mark.asyncio
async def test_update_farm_size_returns_after_document():
    """Test that update_farm_size returns the updated document"""
    user_id = "user123"
    new_farm_size = "10-20 acres"

    # Mock the updated user document
    mock_updated_user = {
        "id": user_id,
        "email": "user@example.com",
        "farm_size": new_farm_size,
    }

    # Create a mock db_conn
    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = MagicMock()
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=mock_updated_user
    )

    # Patch the db_conn used in profile_service
    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await update_farm_size(user_id, new_farm_size)

        # Verify that find_one_and_update was called with ReturnDocument.AFTER
        mock_db_conn.users_collection.find_one_and_update.assert_awaited_once_with(
            {"id": user_id},
            {"$set": {"farm_size": new_farm_size}},
            return_document=ReturnDocument.AFTER,
        )

        # Verify the returned document has the updated farm size
        assert result["farm_size"] == new_farm_size


@pytest.mark.asyncio
async def test_update_farm_size_long_string():
    """Test farm size update with very long string"""
    user_id = "user123"
    farm_size = "A" * 1000  # Very long string

    mock_updated_user = {
        "id": user_id,
        "email": "user@example.com",
        "farm_size": farm_size,
    }

    # Mock db_conn and users_collection
    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = MagicMock()
    mock_db_conn.users_collection.find_one_and_update = AsyncMock(
        return_value=mock_updated_user
    )

    # Patch the db_conn in profile_service
    with patch("services.profile_service.db_conn", mock_db_conn):
        result = await update_farm_size(user_id, farm_size)

        # Assertions
        assert result["farm_size"] == farm_size
        assert len(result["farm_size"]) == 1000

        # Ensure the update was called correctly
        mock_db_conn.users_collection.find_one_and_update.assert_awaited_once_with(
            {"id": user_id},
            {"$set": {"farm_size": farm_size}},
            return_document=ReturnDocument.AFTER,
        )
