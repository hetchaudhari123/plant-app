import pytest
from unittest.mock import AsyncMock, patch, MagicMock, ANY
from datetime import datetime, timezone, timedelta
from services.auth_service import (
    reset_password,
    send_otp,
    logout_user,
    generate_otp_token,
    resend_email_change_otp,
    request_signup_otp,
    resend_signup_otp,
    signup_user,
    login_user,
    change_password,
    reset_password_token,
    refresh_access_token,
)
from fastapi import Request, Response, HTTPException, status
from jose import ExpiredSignatureError, JWTError


# TEST -> send_otp
@pytest.mark.asyncio
async def test_send_otp_success():
    """Test successful OTP generation and sending"""
    email = "test@example.com"
    user_id = "user123"
    purpose = "signup"

    # Mock generate_secure_otp to always return '123456'
    with patch(
        "services.auth_service.generate_secure_otp", return_value="123456"
    ), patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.jinja_env"
    ) as mock_jinja, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ) as mock_send_email, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        # Mock settings
        mock_settings.OTP_EXPIRE_MINUTES = 5

        # Mock MongoDB collection methods
        mock_db.otps_collection.delete_many = AsyncMock()
        mock_db.otps_collection.find_one = AsyncMock(return_value=None)
        mock_db.otps_collection.insert_one = AsyncMock()

        # Mock Jinja template rendering
        mock_template = MagicMock()
        mock_template.render.return_value = "Email body content"
        mock_jinja.get_template.return_value = mock_template

        # Call function
        result = await send_otp(email, user_id=user_id, purpose=purpose)

        # Assertions
        mock_db.otps_collection.delete_many.assert_awaited_once_with({"email": email})
        mock_db.otps_collection.find_one.assert_awaited_once_with({"otp": "123456"})

        # Verify insert_one was called with correct structure
        insert_call = mock_db.otps_collection.insert_one.call_args[0][0]
        assert insert_call["email"] == email
        assert insert_call["otp"] == "123456"
        assert insert_call["user_id"] == user_id
        assert insert_call["purpose"] == purpose
        assert "created_at" in insert_call
        assert "expires_at" in insert_call

        mock_jinja.get_template.assert_called_once_with("email_signup.html")
        mock_template.render.assert_called_once_with(
            email=email, otp="123456", expiry_minutes=5
        )
        mock_send_email.assert_awaited_once_with(
            to_email=email,
            subject="Verify Your Email 🌱",
            body="Email body content",
            is_html=True,
        )

        # Check return value
        assert result["message"] == "OTP sent successfully"
        assert result["email"] == email


@pytest.mark.asyncio
async def test_send_otp_without_optional_params():
    """Test OTP sending without user_id and purpose"""
    email = "test@example.com"

    with patch(
        "services.auth_service.generate_secure_otp", return_value="654321"
    ), patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.jinja_env"
    ) as mock_jinja, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.OTP_EXPIRE_MINUTES = 5
        mock_db.otps_collection.delete_many = AsyncMock()
        mock_db.otps_collection.find_one = AsyncMock(return_value=None)
        mock_db.otps_collection.insert_one = AsyncMock()

        mock_template = MagicMock()
        mock_template.render.return_value = "Email body"
        mock_jinja.get_template.return_value = mock_template

        result = await send_otp(email)

        # Verify insert_one was called without user_id and purpose
        insert_call = mock_db.otps_collection.insert_one.call_args[0][0]
        assert insert_call["email"] == email
        assert insert_call["otp"] == "654321"
        assert "user_id" not in insert_call
        assert "purpose" not in insert_call

        assert result["message"] == "OTP sent successfully"


@pytest.mark.asyncio
async def test_send_otp_unique_otp_generation():
    """Test OTP generation retries when duplicate OTP exists"""
    email = "test@example.com"

    with patch(
        "services.auth_service.generate_secure_otp", side_effect=["111111", "222222"]
    ), patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.jinja_env"
    ) as mock_jinja, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.OTP_EXPIRE_MINUTES = 5
        mock_db.otps_collection.delete_many = AsyncMock()
        # First OTP exists, second doesn't
        mock_db.otps_collection.find_one = AsyncMock(
            side_effect=[{"otp": "111111"}, None]
        )
        mock_db.otps_collection.insert_one = AsyncMock()

        mock_template = MagicMock()
        mock_template.render.return_value = "Email body"
        mock_jinja.get_template.return_value = mock_template

        await send_otp(email)

        # Should have checked twice: once for "111111", once for "222222"
        assert mock_db.otps_collection.find_one.await_count == 2

        # Final inserted OTP should be "222222"
        insert_call = mock_db.otps_collection.insert_one.call_args[0][0]
        assert insert_call["otp"] == "222222"


@pytest.mark.asyncio
async def test_send_otp_fails_after_max_attempts():
    """Test that exception is raised when unique OTP cannot be generated"""
    email = "test@example.com"

    with patch(
        "services.auth_service.generate_secure_otp", return_value="111111"
    ), patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.OTP_EXPIRE_MINUTES = 5
        mock_db.otps_collection.delete_many = AsyncMock()
        # Always return existing OTP (simulating all OTPs are taken)
        mock_db.otps_collection.find_one = AsyncMock(return_value={"otp": "111111"})

        # Should raise exception after 10 attempts
        with pytest.raises(
            Exception, match="Failed to generate a unique OTP after 10 attempts"
        ):
            await send_otp(email)

        # Should have tried 10 times
        assert mock_db.otps_collection.find_one.await_count == 10


@pytest.mark.asyncio
async def test_send_otp_database_error():
    """Test handling of database errors during OTP insertion"""
    email = "test@example.com"

    with patch(
        "services.auth_service.generate_secure_otp", return_value="123456"
    ), patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.OTP_EXPIRE_MINUTES = 5
        mock_db.otps_collection.delete_many = AsyncMock()
        mock_db.otps_collection.find_one = AsyncMock(return_value=None)
        # Simulate database error
        mock_db.otps_collection.insert_one = AsyncMock(
            side_effect=Exception("Database connection error")
        )

        with pytest.raises(Exception, match="Database connection error"):
            await send_otp(email)


@pytest.mark.asyncio
async def test_send_otp_email_sending_failure():
    """Test handling of email sending failures"""
    email = "test@example.com"

    with patch(
        "services.auth_service.generate_secure_otp", return_value="123456"
    ), patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.jinja_env"
    ) as mock_jinja, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ) as mock_send_email, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.OTP_EXPIRE_MINUTES = 5
        mock_db.otps_collection.delete_many = AsyncMock()
        mock_db.otps_collection.find_one = AsyncMock(return_value=None)
        mock_db.otps_collection.insert_one = AsyncMock()

        mock_template = MagicMock()
        mock_template.render.return_value = "Email body"
        mock_jinja.get_template.return_value = mock_template

        # Simulate email sending failure
        mock_send_email.side_effect = Exception("SMTP server unavailable")

        with pytest.raises(Exception, match="SMTP server unavailable"):
            await send_otp(email)

        # OTP should still be inserted before email fails
        mock_db.otps_collection.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_otp_template_rendering_error():
    """Test handling of template rendering errors"""
    email = "test@example.com"

    with patch(
        "services.auth_service.generate_secure_otp", return_value="123456"
    ), patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.jinja_env"
    ) as mock_jinja, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.OTP_EXPIRE_MINUTES = 5
        mock_db.otps_collection.delete_many = AsyncMock()
        mock_db.otps_collection.find_one = AsyncMock(return_value=None)
        mock_db.otps_collection.insert_one = AsyncMock()

        # Simulate template not found
        mock_jinja.get_template.side_effect = Exception("Template not found")

        with pytest.raises(Exception, match="Template not found"):
            await send_otp(email)


@pytest.mark.asyncio
async def test_send_otp_custom_template():
    """Test sending OTP with custom email template"""
    email = "test@example.com"
    custom_template = "password_reset.html"

    with patch(
        "services.auth_service.generate_secure_otp", return_value="999999"
    ), patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.jinja_env"
    ) as mock_jinja, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.OTP_EXPIRE_MINUTES = 5
        mock_db.otps_collection.delete_many = AsyncMock()
        mock_db.otps_collection.find_one = AsyncMock(return_value=None)
        mock_db.otps_collection.insert_one = AsyncMock()

        mock_template = MagicMock()
        mock_template.render.return_value = "Custom email body"
        mock_jinja.get_template.return_value = mock_template

        result = await send_otp(email, email_template=custom_template)

        mock_jinja.get_template.assert_called_once_with(custom_template)
        assert result["message"] == "OTP sent successfully"


# signup user


@pytest.mark.asyncio
async def test_signup_user_success():
    """Test successful user signup with valid OTP"""
    email = "test@example.com"
    otp_code = "123456"
    first_name = "John"
    last_name = "Doe"
    password_hash = "hashed_password_123"

    # Mock OTP entry
    mock_otp_entry = {
        "email": email,
        "otp": otp_code,
        "created_at": datetime.now(timezone.utc),
    }

    # Mock OTP token with pending data
    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "pending_data": {
            "first_name": first_name,
            "last_name": last_name,
            "password_hash": password_hash,
        },
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.Environment"
    ) as mock_env_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ) as mock_send_email:

        # Mock database operations
        mock_db.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
        mock_db.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
        mock_db.users_collection.find_one = AsyncMock(
            return_value=None
        )  # User doesn't exist
        mock_db.users_collection.insert_one = AsyncMock()
        mock_db.otps_collection.delete_many = AsyncMock()
        mock_db.otp_tokens_collection.delete_one = AsyncMock()

        # Mock Jinja2 environment and template
        mock_env = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Welcome Email</html>"
        mock_env.get_template.return_value = mock_template
        mock_env_class.return_value = mock_env

        # Call function
        result = await signup_user(email=email, otp_code=otp_code)

        # Assertions
        assert result["email"] == email
        assert result["first_name"] == first_name
        assert result["last_name"] == last_name
        assert "id" in result
        assert "profile_pic_url" in result
        assert "password_hash" not in result  # Should not return password

        # Verify database calls
        mock_db.otps_collection.find_one.assert_awaited_once_with(
            {"email": email, "otp": otp_code}
        )
        mock_db.otp_tokens_collection.find_one.assert_awaited_once_with(
            {"email": email, "otp_type": "signup"}
        )
        mock_db.users_collection.find_one.assert_awaited_once_with({"email": email})

        # Verify user insertion
        insert_call = mock_db.users_collection.insert_one.call_args[0][0]
        assert insert_call["email"] == email
        assert insert_call["first_name"] == first_name
        assert insert_call["last_name"] == last_name
        assert insert_call["password_hash"] == password_hash
        assert "id" in insert_call
        assert "profile_pic_url" in insert_call

        # Verify cleanup
        mock_db.otps_collection.delete_many.assert_awaited_once_with({"email": email})
        mock_db.otp_tokens_collection.delete_one.assert_awaited_once_with(
            {"_id": mock_otp_token["_id"]}
        )

        # Verify welcome email
        mock_template.render.assert_called_once_with(
            display_name=f"{first_name} {last_name}"
        )
        mock_send_email.assert_awaited_once_with(
            to_email=email,
            subject="Welcome to Plant App 🌱",
            body="<html>Welcome Email</html>",
            is_html=True,
        )


@pytest.mark.asyncio
async def test_signup_user_invalid_otp():
    """Test signup fails with invalid OTP"""
    email = "test@example.com"
    otp_code = "999999"

    with patch("services.auth_service.db_conn") as mock_db:
        # OTP not found
        mock_db.otps_collection.find_one = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await signup_user(email=email, otp_code=otp_code)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid OTP"


@pytest.mark.asyncio
async def test_signup_user_missing_otp_token():
    """Test signup fails when signup session not found"""
    email = "test@example.com"
    otp_code = "123456"

    mock_otp_entry = {"email": email, "otp": otp_code}

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
        # OTP token not found
        mock_db.otp_tokens_collection.find_one = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await signup_user(email=email, otp_code=otp_code)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Signup session not found or expired"


@pytest.mark.asyncio
async def test_signup_user_expired_otp_token():
    """Test signup fails when OTP token has expired"""
    email = "test@example.com"
    otp_code = "123456"

    mock_otp_entry = {"email": email, "otp": otp_code}

    # Expired OTP token
    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) - timedelta(minutes=10),  # Expired
        "pending_data": {
            "first_name": "John",
            "last_name": "Doe",
            "password_hash": "hash",
        },
    }

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
        mock_db.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
        mock_db.otp_tokens_collection.delete_one = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await signup_user(email=email, otp_code=otp_code)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "OTP has expired. Please restart signup process"

        # Verify expired token was deleted
        mock_db.otp_tokens_collection.delete_one.assert_awaited_once_with(
            {"_id": mock_otp_token["_id"]}
        )


@pytest.mark.asyncio
async def test_signup_user_already_exists():
    """Test signup fails when user already exists"""
    email = "test@example.com"
    otp_code = "123456"

    mock_otp_entry = {"email": email, "otp": otp_code}
    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "pending_data": {
            "first_name": "John",
            "last_name": "Doe",
            "password_hash": "hash",
        },
    }

    # Existing user
    existing_user = {"email": email, "id": "user_123"}

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
        mock_db.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
        mock_db.users_collection.find_one = AsyncMock(return_value=existing_user)

        with pytest.raises(HTTPException) as exc_info:
            await signup_user(email=email, otp_code=otp_code)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "User with this email already exists"


@pytest.mark.asyncio
async def test_signup_user_missing_pending_data():
    """Test signup fails when pending_data is missing"""
    email = "test@example.com"
    otp_code = "123456"

    mock_otp_entry = {"email": email, "otp": otp_code}
    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        # Missing pending_data
    }

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
        mock_db.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
        mock_db.users_collection.find_one = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await signup_user(email=email, otp_code=otp_code)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Signup data not found"


@pytest.mark.asyncio
async def test_signup_user_empty_pending_data():
    """Test signup fails when pending_data is empty"""
    email = "test@example.com"
    otp_code = "123456"

    mock_otp_entry = {"email": email, "otp": otp_code}
    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "pending_data": None,  # Empty pending_data
    }

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
        mock_db.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
        mock_db.users_collection.find_one = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await signup_user(email=email, otp_code=otp_code)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Signup data not found"


@pytest.mark.asyncio
async def test_signup_user_database_insert_error():
    """Test handling of database insertion errors"""
    email = "test@example.com"
    otp_code = "123456"

    mock_otp_entry = {"email": email, "otp": otp_code}
    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "pending_data": {
            "first_name": "John",
            "last_name": "Doe",
            "password_hash": "hash",
        },
    }

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
        mock_db.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
        mock_db.users_collection.find_one = AsyncMock(return_value=None)
        # Database insert fails
        mock_db.users_collection.insert_one = AsyncMock(
            side_effect=Exception("Database connection error")
        )

        with pytest.raises(Exception, match="Database connection error"):
            await signup_user(email=email, otp_code=otp_code)


@pytest.mark.asyncio
async def test_signup_user_welcome_email_failure():
    """Test that signup completes even if welcome email fails"""
    email = "test@example.com"
    otp_code = "123456"

    mock_otp_entry = {"email": email, "otp": otp_code}
    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "pending_data": {
            "first_name": "John",
            "last_name": "Doe",
            "password_hash": "hash",
        },
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.Environment"
    ) as mock_env_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ) as mock_send_email:

        mock_db.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
        mock_db.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
        mock_db.users_collection.find_one = AsyncMock(return_value=None)
        mock_db.users_collection.insert_one = AsyncMock()
        mock_db.otps_collection.delete_many = AsyncMock()
        mock_db.otp_tokens_collection.delete_one = AsyncMock()

        mock_env = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Welcome</html>"
        mock_env.get_template.return_value = mock_template
        mock_env_class.return_value = mock_env

        # Email sending fails
        mock_send_email.side_effect = Exception("SMTP error")

        with pytest.raises(Exception, match="SMTP error"):
            await signup_user(email=email, otp_code=otp_code)

        # User should still be created and cleanup should happen
        mock_db.users_collection.insert_one.assert_awaited_once()
        mock_db.otps_collection.delete_many.assert_awaited_once()
        mock_db.otp_tokens_collection.delete_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_signup_user_profile_pic_url_generation():
    """Test correct profile picture URL generation with special characters"""
    email = "test@example.com"
    otp_code = "123456"
    first_name = "José"
    last_name = "García"

    mock_otp_entry = {"email": email, "otp": otp_code}
    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "pending_data": {
            "first_name": first_name,
            "last_name": last_name,
            "password_hash": "hash",
        },
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.Environment"
    ) as mock_env_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ):

        mock_db.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
        mock_db.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
        mock_db.users_collection.find_one = AsyncMock(return_value=None)
        mock_db.users_collection.insert_one = AsyncMock()
        mock_db.otps_collection.delete_many = AsyncMock()
        mock_db.otp_tokens_collection.delete_one = AsyncMock()

        mock_env = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Welcome</html>"
        mock_env.get_template.return_value = mock_template
        mock_env_class.return_value = mock_env

        result = await signup_user(email=email, otp_code=otp_code)

        # Verify profile pic URL is generated correctly
        assert (
            "https://api.dicebear.com/5.x/initials/svg?seed="
            in result["profile_pic_url"]
        )
        assert first_name in result["profile_pic_url"]
        assert last_name in result["profile_pic_url"]


@pytest.mark.asyncio
async def test_signup_user_cleanup_on_success():
    """Test that OTP and token are properly cleaned up after successful signup"""
    email = "test@example.com"
    otp_code = "123456"
    token_id = "token_id_123"

    mock_otp_entry = {"email": email, "otp": otp_code}
    mock_otp_token = {
        "_id": token_id,
        "email": email,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "pending_data": {
            "first_name": "John",
            "last_name": "Doe",
            "password_hash": "hash",
        },
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.Environment"
    ) as mock_env_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ):

        mock_db.otps_collection.find_one = AsyncMock(return_value=mock_otp_entry)
        mock_db.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
        mock_db.users_collection.find_one = AsyncMock(return_value=None)
        mock_db.users_collection.insert_one = AsyncMock()
        mock_db.otps_collection.delete_many = AsyncMock()
        mock_db.otp_tokens_collection.delete_one = AsyncMock()

        mock_env = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Welcome</html>"
        mock_env.get_template.return_value = mock_template
        mock_env_class.return_value = mock_env

        await signup_user(email=email, otp_code=otp_code)

        # Verify cleanup happened
        mock_db.otps_collection.delete_many.assert_awaited_once_with({"email": email})
        mock_db.otp_tokens_collection.delete_one.assert_awaited_once_with(
            {"_id": token_id}
        )


@pytest.mark.asyncio
async def test_login_user_success():
    """Test successful user login with valid credentials"""
    email = "test@example.com"
    password = "correct_password"
    user_id = "user_123"
    token_version = 1

    mock_user = {
        "id": user_id,
        "email": email,
        "first_name": "John",
        "last_name": "Doe",
        "profile_pic_url": "https://example.com/pic.jpg",
        "password_hash": "hashed_password",
        "token_version": token_version,
    }

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ) as mock_verify, patch(
        "services.auth_service.create_access_token", return_value="access_token_123"
    ) as mock_access, patch(
        "services.auth_service.create_refresh_token", return_value="refresh_token_456"
    ) as mock_refresh, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user.copy())
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        # Call function
        result = await login_user(
            email=email, password=password, response=mock_response
        )

        # Assertions
        assert result["id"] == user_id
        assert result["email"] == email
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert "password_hash" not in result  # Should be removed

        # Verify database query
        mock_db.users_collection.find_one.assert_awaited_once_with({"email": email})

        # Verify password verification
        mock_verify.assert_called_once_with(password, "hashed_password")

        # Verify token creation
        mock_access.assert_called_once_with(user_id, token_version)
        mock_refresh.assert_called_once_with(user_id, token_version)

        # Verify cookies are set
        assert mock_response.set_cookie.call_count == 2

        # Check access token cookie
        access_cookie_call = mock_response.set_cookie.call_args_list[0]
        assert access_cookie_call[1]["key"] == "access_token"
        assert access_cookie_call[1]["value"] == "access_token_123"
        assert access_cookie_call[1]["httponly"] is True
        assert access_cookie_call[1]["secure"] is True
        assert access_cookie_call[1]["samesite"] == "none"
        assert access_cookie_call[1]["max_age"] == 15 * 60

        # Check refresh token cookie
        refresh_cookie_call = mock_response.set_cookie.call_args_list[1]
        assert refresh_cookie_call[1]["key"] == "refresh_token"
        assert refresh_cookie_call[1]["value"] == "refresh_token_456"
        assert refresh_cookie_call[1]["httponly"] is True
        assert refresh_cookie_call[1]["secure"] is True
        assert refresh_cookie_call[1]["samesite"] == "none"
        assert refresh_cookie_call[1]["max_age"] == 7 * 24 * 60 * 60


@pytest.mark.asyncio
async def test_login_user_with_default_token_version():
    """Test login when user has no token_version (defaults to 0)"""
    email = "test@example.com"
    password = "password123"

    mock_user = {
        "id": "user_123",
        "email": email,
        "password_hash": "hashed_password",
        # No token_version field
    }

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ), patch("services.auth_service.create_access_token") as mock_access, patch(
        "services.auth_service.create_refresh_token"
    ) as mock_refresh, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user.copy())
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        await login_user(email=email, password=password, response=mock_response)

        # Should use default token_version of 0
        mock_access.assert_called_once_with("user_123", 0)
        mock_refresh.assert_called_once_with("user_123", 0)


@pytest.mark.asyncio
async def test_login_user_not_found():
    """Test login fails when user doesn't exist"""
    email = "nonexistent@example.com"
    password = "password123"
    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.users_collection.find_one = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="User with the given email not found"):
            await login_user(email=email, password=password, response=mock_response)


@pytest.mark.asyncio
async def test_login_user_incorrect_password():
    """Test login fails with incorrect password"""
    email = "test@example.com"
    password = "wrong_password"

    mock_user = {"id": "user_123", "email": email, "password_hash": "hashed_password"}

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=False
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        with pytest.raises(ValueError, match="Passwords do not match"):
            await login_user(email=email, password=password, response=mock_response)


@pytest.mark.asyncio
async def test_login_user_database_error():
    """Test login handles database errors"""
    email = "test@example.com"
    password = "password123"
    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.users_collection.find_one = AsyncMock(
            side_effect=Exception("Database connection error")
        )

        with pytest.raises(Exception, match="Database connection error"):
            await login_user(email=email, password=password, response=mock_response)


@pytest.mark.asyncio
async def test_login_user_password_hash_removed():
    """Test that password_hash is removed from returned user object"""
    email = "test@example.com"
    password = "password123"

    mock_user = {
        "id": "user_123",
        "email": email,
        "password_hash": "hashed_password",
        "token_version": 0,
    }

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ), patch("services.auth_service.create_access_token", return_value="token"), patch(
        "services.auth_service.create_refresh_token", return_value="token"
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user.copy())
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        result = await login_user(
            email=email, password=password, response=mock_response
        )

        assert "password_hash" not in result
        assert result["id"] == "user_123"
        assert result["email"] == email


@pytest.mark.asyncio
async def test_login_user_token_creation_error():
    """Test login handles token creation errors"""
    email = "test@example.com"
    password = "password123"

    mock_user = {
        "id": "user_123",
        "email": email,
        "password_hash": "hashed_password",
        "token_version": 0,
    }

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ), patch(
        "services.auth_service.create_access_token",
        side_effect=Exception("Token creation failed"),
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        with pytest.raises(Exception, match="Token creation failed"):
            await login_user(email=email, password=password, response=mock_response)


@pytest.mark.asyncio
async def test_login_user_cookie_settings():
    """Test that cookies are set with correct security settings"""
    email = "test@example.com"
    password = "password123"

    mock_user = {
        "id": "user_123",
        "email": email,
        "password_hash": "hashed_password",
        "token_version": 0,
    }

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ), patch(
        "services.auth_service.create_access_token", return_value="access_123"
    ), patch(
        "services.auth_service.create_refresh_token", return_value="refresh_456"
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user.copy())
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 14

        await login_user(email=email, password=password, response=mock_response)

        # Verify both cookies have correct security settings
        for call in mock_response.set_cookie.call_args_list:
            kwargs = call[1]
            assert kwargs["httponly"] is True, "Cookie should be httponly"
            assert kwargs["secure"] is True, "Cookie should be secure"
            assert kwargs["samesite"] == "none", "Cookie should have samesite=none"


@pytest.mark.asyncio
async def test_login_user_id_converted_to_string():
    """Test that user ID is properly converted to string for token creation"""
    email = "test@example.com"
    password = "password123"

    # User ID as ObjectId or other non-string type
    mock_user = {
        "id": 12345,  # Integer ID
        "email": email,
        "password_hash": "hashed_password",
        "token_version": 0,
    }

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ), patch("services.auth_service.create_access_token") as mock_access, patch(
        "services.auth_service.create_refresh_token"
    ) as mock_refresh, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user.copy())
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        await login_user(email=email, password=password, response=mock_response)

        # Verify ID is converted to string
        mock_access.assert_called_once_with("12345", 0)
        mock_refresh.assert_called_once_with("12345", 0)


@pytest.mark.asyncio
async def test_change_password_success():
    """Test successful password change"""
    user_id = "user_123"
    old_password = "old_password123"
    new_password = "new_password456"
    confirm_password = "new_password456"

    mock_user = {
        "id": user_id,
        "email": "test@example.com",
        "password_hash": "old_hashed_password",
        "token_version": 0,
    }

    updated_user = {
        "id": user_id,
        "email": "test@example.com",
        "password_hash": "new_hashed_password",
        "token_version": 1,
    }

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ) as mock_verify, patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ) as mock_hash, patch(
        "services.auth_service.create_access_token", return_value="new_access_token"
    ) as mock_access, patch(
        "services.auth_service.create_refresh_token", return_value="new_refresh_token"
    ) as mock_refresh, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        # Call function
        await change_password(
            user_id=user_id,
            old_password=old_password,
            new_password=new_password,
            confirm_password=confirm_password,
            response=mock_response,
        )

        # Verify user lookup
        mock_db.users_collection.find_one.assert_awaited_once_with({"id": user_id})

        # Verify old password verification
        mock_verify.assert_called_once_with(old_password, "old_hashed_password")

        # Verify new password hashing
        mock_hash.assert_called_once_with(new_password)

        # Verify database update
        mock_db.users_collection.find_one_and_update.assert_awaited_once()
        update_call = mock_db.users_collection.find_one_and_update.call_args
        assert update_call[0][0] == {"id": user_id}
        assert update_call[0][1] == {
            "$set": {"password_hash": "new_hashed_password"},
            "$inc": {"token_version": 1},
        }
        assert update_call[1]["return_document"] is True

        # Verify old cookies deleted
        assert mock_response.delete_cookie.call_count == 2
        mock_response.delete_cookie.assert_any_call("access_token")
        mock_response.delete_cookie.assert_any_call("refresh_token")

        # Verify new tokens created with incremented version
        mock_access.assert_called_once_with(user_id, 1)
        mock_refresh.assert_called_once_with(user_id, 1)

        # Verify new cookies set
        assert mock_response.set_cookie.call_count == 2
        access_cookie_call = mock_response.set_cookie.call_args_list[0]
        assert access_cookie_call[1]["key"] == "access_token"
        assert access_cookie_call[1]["value"] == "new_access_token"
        assert access_cookie_call[1]["httponly"] is True
        assert access_cookie_call[1]["secure"] is True
        assert access_cookie_call[1]["samesite"] == "none"

        refresh_cookie_call = mock_response.set_cookie.call_args_list[1]
        assert refresh_cookie_call[1]["key"] == "refresh_token"
        assert refresh_cookie_call[1]["value"] == "new_refresh_token"


@pytest.mark.asyncio
async def test_change_password_user_not_found():
    """Test password change fails when user doesn't exist"""
    user_id = "nonexistent_user"
    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.users_collection.find_one = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await change_password(
                user_id=user_id,
                old_password="old_pass",
                new_password="new_pass",
                confirm_password="new_pass",
                response=mock_response,
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_change_password_incorrect_old_password():
    """Test password change fails with incorrect old password"""
    user_id = "user_123"
    old_password = "wrong_old_password"
    new_password = "new_password456"
    confirm_password = "new_password456"

    mock_user = {"id": user_id, "password_hash": "correct_old_hashed_password"}

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=False
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        with pytest.raises(HTTPException) as exc_info:
            await change_password(
                user_id=user_id,
                old_password=old_password,
                new_password=new_password,
                confirm_password=confirm_password,
                response=mock_response,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Old password is incorrect"


@pytest.mark.asyncio
async def test_change_password_mismatch_confirmation():
    """Test password change fails when new password and confirmation don't match"""
    user_id = "user_123"
    old_password = "old_password123"
    new_password = "new_password456"
    confirm_password = "different_password789"

    mock_user = {"id": user_id, "password_hash": "old_hashed_password"}

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        with pytest.raises(HTTPException) as exc_info:
            await change_password(
                user_id=user_id,
                old_password=old_password,
                new_password=new_password,
                confirm_password=confirm_password,
                response=mock_response,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "New password and confirm password do not match"


@pytest.mark.asyncio
async def test_change_password_database_update_error():
    """Test password change handles database update errors"""
    user_id = "user_123"
    old_password = "old_password123"
    new_password = "new_password456"
    confirm_password = "new_password456"

    mock_user = {"id": user_id, "password_hash": "old_hashed_password"}

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ), patch("services.auth_service.hash_password", return_value="new_hashed_password"):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            side_effect=Exception("Database update failed")
        )

        with pytest.raises(Exception, match="Database update failed"):
            await change_password(
                user_id=user_id,
                old_password=old_password,
                new_password=new_password,
                confirm_password=confirm_password,
                response=mock_response,
            )


@pytest.mark.asyncio
async def test_change_password_token_version_increment():
    """Test that token_version is properly incremented"""
    user_id = "user_123"

    mock_user = {
        "id": user_id,
        "password_hash": "old_hashed_password",
        "token_version": 5,
    }

    updated_user = {
        "id": user_id,
        "password_hash": "new_hashed_password",
        "token_version": 6,
    }

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ), patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ), patch(
        "services.auth_service.create_access_token"
    ) as mock_access, patch(
        "services.auth_service.create_refresh_token"
    ) as mock_refresh, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        await change_password(
            user_id=user_id,
            old_password="old_pass",
            new_password="new_pass",
            confirm_password="new_pass",
            response=mock_response,
        )

        # Verify tokens created with new version (6)
        mock_access.assert_called_once_with(user_id, 6)
        mock_refresh.assert_called_once_with(user_id, 6)


@pytest.mark.asyncio
async def test_change_password_token_creation_error():
    """Test password change handles token creation errors"""
    user_id = "user_123"

    mock_user = {
        "id": user_id,
        "password_hash": "old_hashed_password",
        "token_version": 0,
    }

    updated_user = {
        "id": user_id,
        "password_hash": "new_hashed_password",
        "token_version": 1,
    }

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ), patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ), patch(
        "services.auth_service.create_access_token",
        side_effect=Exception("Token creation failed"),
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )

        with pytest.raises(Exception, match="Token creation failed"):
            await change_password(
                user_id=user_id,
                old_password="old_pass",
                new_password="new_pass",
                confirm_password="new_pass",
                response=mock_response,
            )


@pytest.mark.asyncio
async def test_change_password_same_as_old():
    """Test that user can set new password same as old (if allowed by business logic)"""
    user_id = "user_123"
    password = "same_password123"

    mock_user = {"id": user_id, "password_hash": "hashed_password", "token_version": 0}

    updated_user = {
        "id": user_id,
        "password_hash": "hashed_password",
        "token_version": 1,
    }

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ), patch(
        "services.auth_service.hash_password", return_value="hashed_password"
    ), patch(
        "services.auth_service.create_access_token", return_value="token"
    ), patch(
        "services.auth_service.create_refresh_token", return_value="token"
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        # Should complete successfully
        await change_password(
            user_id=user_id,
            old_password=password,
            new_password=password,
            confirm_password=password,
            response=mock_response,
        )

        # Verify token version was still incremented
        mock_db.users_collection.find_one_and_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_password_cookie_deletion_order():
    """Test that old cookies are deleted before new ones are set"""
    user_id = "user_123"

    mock_user = {
        "id": user_id,
        "password_hash": "old_hashed_password",
        "token_version": 0,
    }

    updated_user = {
        "id": user_id,
        "password_hash": "new_hashed_password",
        "token_version": 1,
    }

    mock_response = MagicMock(spec=Response)
    call_order = []

    def track_delete(key):
        call_order.append(f"delete_{key}")

    def track_set(**kwargs):
        call_order.append(f"set_{kwargs['key']}")

    mock_response.delete_cookie.side_effect = track_delete
    mock_response.set_cookie.side_effect = track_set

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ), patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ), patch(
        "services.auth_service.create_access_token", return_value="token"
    ), patch(
        "services.auth_service.create_refresh_token", return_value="token"
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        await change_password(
            user_id=user_id,
            old_password="old_pass",
            new_password="new_pass",
            confirm_password="new_pass",
            response=mock_response,
        )

        # Verify deletion happens before setting
        assert "delete_access_token" in call_order
        assert "delete_refresh_token" in call_order
        assert "set_access_token" in call_order
        assert "set_refresh_token" in call_order

        delete_indices = [
            call_order.index("delete_access_token"),
            call_order.index("delete_refresh_token"),
        ]
        set_indices = [
            call_order.index("set_access_token"),
            call_order.index("set_refresh_token"),
        ]

        assert max(delete_indices) < min(
            set_indices
        ), "Cookies should be deleted before new ones are set"


@pytest.mark.asyncio
async def test_change_password_atomic_operation():
    """Test that password update and token version increment happen atomically"""
    user_id = "user_123"

    mock_user = {
        "id": user_id,
        "password_hash": "old_hashed_password",
        "token_version": 0,
    }

    updated_user = {
        "id": user_id,
        "password_hash": "new_hashed_password",
        "token_version": 1,
    }

    mock_response = MagicMock(spec=Response)

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.verify_password", return_value=True
    ), patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ), patch(
        "services.auth_service.create_access_token", return_value="token"
    ), patch(
        "services.auth_service.create_refresh_token", return_value="token"
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        await change_password(
            user_id=user_id,
            old_password="old_pass",
            new_password="new_pass",
            confirm_password="new_pass",
            response=mock_response,
        )

        # Verify single atomic operation with both $set and $inc
        update_call = mock_db.users_collection.find_one_and_update.call_args[0]
        assert "$set" in update_call[1]
        assert "$inc" in update_call[1]
        assert update_call[1]["$set"]["password_hash"] == "new_hashed_password"
        assert update_call[1]["$inc"]["token_version"] == 1


@pytest.mark.asyncio
async def test_reset_password_token_success():
    """Test successful password reset token generation and email sending"""
    email = "test@example.com"
    user_id = "user_123"
    generated_token = "secure_random_token_abc123"

    mock_user = {
        "id": user_id,
        "email": email,
        "first_name": "John",
        "last_name": "Doe",
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.secrets.token_urlsafe", return_value=generated_token
    ) as mock_token, patch(
        "services.auth_service.Jinja2Templates"
    ) as mock_jinja_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ) as mock_send_email, patch(
        "services.auth_service.settings"
    ) as mock_settings, patch(
        "services.auth_service.datetime"
    ) as mock_datetime:

        # Mock settings
        mock_settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES = 30
        mock_settings.FRONTEND_URL = "https://example.com"

        # Mock datetime
        fixed_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        # Mock database operations
        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.update_one = AsyncMock()

        # Mock Jinja2 template
        mock_templates = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Reset password email</html>"
        mock_templates.get_template.return_value = mock_template
        mock_jinja_class.return_value = mock_templates

        # Call function
        await reset_password_token(email=email)

        # Verify user lookup
        mock_db.users_collection.find_one.assert_awaited_once_with({"email": email})

        # Verify token generation
        mock_token.assert_called_once_with(32)

        # Verify database update with token and expiry
        expected_expires_at = fixed_now + timedelta(minutes=30)
        mock_db.users_collection.update_one.assert_awaited_once_with(
            {"id": user_id},
            {
                "$set": {
                    "reset_token": generated_token,
                    "reset_token_expires_at": expected_expires_at,
                }
            },
        )

        # Verify template rendering
        mock_jinja_class.assert_called_once_with(directory="templates")
        mock_templates.get_template.assert_called_once_with(
            "email_forget_password.html"
        )
        mock_template.render.assert_called_once_with(
            user_name="John",
            reset_link=f"https://example.com/update-password/{generated_token}",
            current_year=fixed_now.year,
        )

        # Verify email sending
        mock_send_email.assert_awaited_once_with(
            to_email=email,
            subject="Reset Your Password",
            body="<html>Reset password email</html>",
        )


@pytest.mark.asyncio
async def test_reset_password_token_user_not_found():
    """Test password reset fails when user doesn't exist"""
    email = "nonexistent@example.com"

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.Jinja2Templates"
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await reset_password_token(email=email)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_reset_password_token_without_first_name():
    """Test password reset when user has no first_name"""
    email = "test@example.com"
    user_id = "user_123"
    generated_token = "secure_token_xyz"

    mock_user = {
        "id": user_id,
        "email": email,
        # No first_name field
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.secrets.token_urlsafe", return_value=generated_token
    ), patch("services.auth_service.Jinja2Templates") as mock_jinja_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings, patch(
        "services.auth_service.datetime"
    ) as mock_datetime:

        mock_settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES = 30
        mock_settings.FRONTEND_URL = "https://example.com"

        fixed_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.update_one = AsyncMock()

        mock_templates = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Email</html>"
        mock_templates.get_template.return_value = mock_template
        mock_jinja_class.return_value = mock_templates

        await reset_password_token(email=email)

        # Verify template rendered with empty string for user_name
        mock_template.render.assert_called_once()
        render_call = mock_template.render.call_args[1]
        assert render_call["user_name"] == ""


@pytest.mark.asyncio
async def test_reset_password_token_replaces_existing_token():
    """Test that existing reset token is replaced with new one"""
    email = "test@example.com"
    user_id = "user_123"
    new_token = "new_secure_token"

    mock_user = {
        "id": user_id,
        "email": email,
        "first_name": "John",
        "reset_token": "old_token_123",  # Existing token
        "reset_token_expires_at": datetime.now(timezone.utc)
        - timedelta(hours=1),  # Expired
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.secrets.token_urlsafe", return_value=new_token
    ), patch("services.auth_service.Jinja2Templates") as mock_jinja_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings, patch(
        "services.auth_service.datetime"
    ) as mock_datetime:

        mock_settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES = 30
        mock_settings.FRONTEND_URL = "https://example.com"

        fixed_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.update_one = AsyncMock()

        mock_templates = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Email</html>"
        mock_templates.get_template.return_value = mock_template
        mock_jinja_class.return_value = mock_templates

        await reset_password_token(email=email)

        # Verify new token replaces old one
        update_call = mock_db.users_collection.update_one.call_args[0]
        assert update_call[1]["$set"]["reset_token"] == new_token
        assert update_call[1]["$set"]["reset_token"] != "old_token_123"


@pytest.mark.asyncio
async def test_reset_password_token_url_construction():
    """Test correct reset URL construction"""
    email = "test@example.com"
    user_id = "user_123"
    generated_token = "abc123def456"

    mock_user = {"id": user_id, "email": email, "first_name": "John"}

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.secrets.token_urlsafe", return_value=generated_token
    ), patch("services.auth_service.Jinja2Templates") as mock_jinja_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings, patch(
        "services.auth_service.datetime"
    ) as mock_datetime:

        mock_settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES = 30
        mock_settings.FRONTEND_URL = "https://myapp.com"

        fixed_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.update_one = AsyncMock()

        mock_templates = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Email</html>"
        mock_templates.get_template.return_value = mock_template
        mock_jinja_class.return_value = mock_templates

        await reset_password_token(email=email)

        # Verify correct URL format
        render_call = mock_template.render.call_args[1]
        expected_url = f"https://myapp.com/update-password/{generated_token}"
        assert render_call["reset_link"] == expected_url


@pytest.mark.asyncio
async def test_reset_password_token_expiry_time_calculation():
    """Test correct expiry time calculation"""
    email = "test@example.com"
    user_id = "user_123"

    mock_user = {"id": user_id, "email": email, "first_name": "John"}

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.secrets.token_urlsafe", return_value="token"
    ), patch("services.auth_service.Jinja2Templates") as mock_jinja_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings, patch(
        "services.auth_service.datetime"
    ) as mock_datetime:

        mock_settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES = 45
        mock_settings.FRONTEND_URL = "https://example.com"

        fixed_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.update_one = AsyncMock()

        mock_templates = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Email</html>"
        mock_templates.get_template.return_value = mock_template
        mock_jinja_class.return_value = mock_templates

        await reset_password_token(email=email)

        # Verify expiry time is exactly 45 minutes from now
        update_call = mock_db.users_collection.update_one.call_args[0]
        expected_expires_at = fixed_now + timedelta(minutes=45)
        assert update_call[1]["$set"]["reset_token_expires_at"] == expected_expires_at


@pytest.mark.asyncio
async def test_reset_password_token_database_update_error():
    """Test handling of database update errors"""
    email = "test@example.com"

    mock_user = {"id": "user_123", "email": email, "first_name": "John"}

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.secrets.token_urlsafe", return_value="token"
    ), patch("services.auth_service.Jinja2Templates"), patch(
        "services.auth_service.settings"
    ) as mock_settings, patch(
        "services.auth_service.datetime"
    ) as mock_datetime:

        mock_settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES = 30

        fixed_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.update_one = AsyncMock(
            side_effect=Exception("Database update failed")
        )

        with pytest.raises(Exception, match="Database update failed"):
            await reset_password_token(email=email)


@pytest.mark.asyncio
async def test_reset_password_token_email_sending_error():
    """Test handling of email sending errors"""
    email = "test@example.com"

    mock_user = {"id": "user_123", "email": email, "first_name": "John"}

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.secrets.token_urlsafe", return_value="token"
    ), patch("services.auth_service.Jinja2Templates") as mock_jinja_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ) as mock_send_email, patch(
        "services.auth_service.settings"
    ) as mock_settings, patch(
        "services.auth_service.datetime"
    ) as mock_datetime:

        mock_settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES = 30
        mock_settings.FRONTEND_URL = "https://example.com"

        fixed_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.update_one = AsyncMock()

        mock_templates = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Email</html>"
        mock_templates.get_template.return_value = mock_template
        mock_jinja_class.return_value = mock_templates

        # Email sending fails
        mock_send_email.side_effect = Exception("SMTP server unavailable")

        with pytest.raises(Exception, match="SMTP server unavailable"):
            await reset_password_token(email=email)

        # Token should still be saved in database
        mock_db.users_collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_reset_password_token_template_not_found():
    """Test handling of missing email template"""
    email = "test@example.com"

    mock_user = {"id": "user_123", "email": email, "first_name": "John"}

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.secrets.token_urlsafe", return_value="token"
    ), patch("services.auth_service.Jinja2Templates") as mock_jinja_class, patch(
        "services.auth_service.settings"
    ) as mock_settings, patch(
        "services.auth_service.datetime"
    ) as mock_datetime:

        mock_settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES = 30
        mock_settings.FRONTEND_URL = "https://example.com"

        fixed_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.update_one = AsyncMock()

        mock_templates = MagicMock()
        mock_templates.get_template.side_effect = Exception(
            "Template not found: email_forget_password.html"
        )
        mock_jinja_class.return_value = mock_templates

        with pytest.raises(Exception, match="Template not found"):
            await reset_password_token(email=email)


@pytest.mark.asyncio
async def test_reset_password_token_secure_token_generation():
    """Test that token is generated using secure method"""
    email = "test@example.com"

    mock_user = {"id": "user_123", "email": email, "first_name": "John"}

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.secrets.token_urlsafe"
    ) as mock_token_gen, patch(
        "services.auth_service.Jinja2Templates"
    ) as mock_jinja_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings, patch(
        "services.auth_service.datetime"
    ) as mock_datetime:

        mock_settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES = 30
        mock_settings.FRONTEND_URL = "https://example.com"

        fixed_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        mock_token_gen.return_value = "secure_random_token"
        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.update_one = AsyncMock()

        mock_templates = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Email</html>"
        mock_templates.get_template.return_value = mock_template
        mock_jinja_class.return_value = mock_templates

        await reset_password_token(email=email)

        # Verify secrets.token_urlsafe is used with 32 bytes
        mock_token_gen.assert_called_once_with(32)


@pytest.mark.asyncio
async def test_reset_password_token_current_year_in_template():
    """Test that current year is passed to template"""
    email = "test@example.com"

    mock_user = {"id": "user_123", "email": email, "first_name": "John"}

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.secrets.token_urlsafe", return_value="token"
    ), patch("services.auth_service.Jinja2Templates") as mock_jinja_class, patch(
        "services.auth_service.send_email", new_callable=AsyncMock
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings, patch(
        "services.auth_service.datetime"
    ) as mock_datetime:

        mock_settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES = 30
        mock_settings.FRONTEND_URL = "https://example.com"

        fixed_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.update_one = AsyncMock()

        mock_templates = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Email</html>"
        mock_templates.get_template.return_value = mock_template
        mock_jinja_class.return_value = mock_templates

        await reset_password_token(email=email)

        # Verify current year is passed to template
        render_call = mock_template.render.call_args[1]
        assert render_call["current_year"] == 2025


@pytest.mark.asyncio
async def test_reset_password_success():
    """Test successful password reset with valid token"""
    token = "valid_reset_token_abc123"
    password = "new_secure_password"
    confirm_password = "new_secure_password"
    user_id = "user_123"

    mock_user = {
        "id": user_id,
        "email": "test@example.com",
        "reset_token": token,
        "reset_token_expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "token_version": 2,
    }

    updated_user = {
        "id": user_id,
        "email": "test@example.com",
        "password_hash": "new_hashed_password",
        "token_version": 3,
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ) as mock_hash:

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )
        mock_db.users_collection.update_one = AsyncMock()

        # Call function
        await reset_password(
            token=token, password=password, confirm_password=confirm_password
        )

        # Verify user lookup by token
        mock_db.users_collection.find_one.assert_awaited_once_with(
            {"reset_token": token}
        )

        # Verify password hashing
        mock_hash.assert_called_once_with(password)

        # Verify password update and token version increment
        update_call = mock_db.users_collection.find_one_and_update.call_args
        assert update_call[0][0] == {"id": user_id}
        assert update_call[0][1] == {
            "$set": {"password_hash": "new_hashed_password"},
            "$inc": {"token_version": 1},
        }
        assert update_call[1]["return_document"] is True

        # Verify reset token cleanup
        cleanup_call = mock_db.users_collection.update_one.call_args
        assert cleanup_call[0][0] == {"id": user_id}
        assert cleanup_call[0][1] == {
            "$set": {"reset_token": None, "reset_token_expires_at": None}
        }


@pytest.mark.asyncio
async def test_reset_password_mismatch():
    """Test password reset fails when passwords don't match"""
    token = "valid_token"
    password = "new_password123"
    confirm_password = "different_password456"

    with pytest.raises(HTTPException) as exc_info:
        await reset_password(
            token=token, password=password, confirm_password=confirm_password
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Passwords do not match"


@pytest.mark.asyncio
async def test_reset_password_invalid_token():
    """Test password reset fails with invalid token"""
    token = "invalid_token_xyz"
    password = "new_password123"
    confirm_password = "new_password123"

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.users_collection.find_one = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(
                token=token, password=password, confirm_password=confirm_password
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Invalid reset token"


@pytest.mark.asyncio
async def test_reset_password_expired_token():
    """Test password reset fails when token is expired"""
    token = "expired_token"
    password = "new_password123"
    confirm_password = "new_password123"

    mock_user = {
        "id": "user_123",
        "email": "test@example.com",
        "reset_token": token,
        "reset_token_expires_at": datetime.now(timezone.utc)
        - timedelta(hours=1),  # Expired
    }

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(
                token=token, password=password, confirm_password=confirm_password
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Reset token expired"


@pytest.mark.asyncio
async def test_reset_password_missing_expiry():
    """Test password reset fails when expiry is missing"""
    token = "valid_token"
    password = "new_password123"
    confirm_password = "new_password123"

    mock_user = {
        "id": "user_123",
        "email": "test@example.com",
        "reset_token": token,
        # Missing reset_token_expires_at
    }

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(
                token=token, password=password, confirm_password=confirm_password
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Reset token expired"


@pytest.mark.asyncio
async def test_reset_password_null_expiry():
    """Test password reset fails when expiry is None"""
    token = "valid_token"
    password = "new_password123"
    confirm_password = "new_password123"

    mock_user = {
        "id": "user_123",
        "email": "test@example.com",
        "reset_token": token,
        "reset_token_expires_at": None,
    }

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(
                token=token, password=password, confirm_password=confirm_password
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Reset token expired"


@pytest.mark.asyncio
async def test_reset_password_iso_string_expiry():
    """Test password reset handles ISO string datetime format"""
    token = "valid_token"
    password = "new_password123"
    confirm_password = "new_password123"

    # Future expiry as ISO string
    future_expiry = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    mock_user = {
        "id": "user_123",
        "email": "test@example.com",
        "reset_token": token,
        "reset_token_expires_at": future_expiry,  # ISO string format
        "token_version": 0,
    }

    updated_user = {
        "id": "user_123",
        "password_hash": "new_hashed_password",
        "token_version": 1,
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )
        mock_db.users_collection.update_one = AsyncMock()

        # Should complete successfully
        await reset_password(
            token=token, password=password, confirm_password=confirm_password
        )

        mock_db.users_collection.find_one_and_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_reset_password_naive_datetime_expiry():
    """Test password reset handles naive datetime (no timezone info)"""
    token = "valid_token"
    password = "new_password123"
    confirm_password = "new_password123"

    # Future expiry as naive datetime
    naive_expiry = datetime.now() + timedelta(hours=1)

    mock_user = {
        "id": "user_123",
        "email": "test@example.com",
        "reset_token": token,
        "reset_token_expires_at": naive_expiry,  # Naive datetime
        "token_version": 0,
    }

    updated_user = {
        "id": "user_123",
        "password_hash": "new_hashed_password",
        "token_version": 1,
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )
        mock_db.users_collection.update_one = AsyncMock()

        # Should complete successfully (naive datetime converted to UTC)
        await reset_password(
            token=token, password=password, confirm_password=confirm_password
        )

        mock_db.users_collection.find_one_and_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_reset_password_expired_iso_string():
    """Test password reset fails with expired ISO string datetime"""
    token = "expired_token"
    password = "new_password123"
    confirm_password = "new_password123"

    # Past expiry as ISO string
    past_expiry = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    mock_user = {
        "id": "user_123",
        "email": "test@example.com",
        "reset_token": token,
        "reset_token_expires_at": past_expiry,
    }

    with patch("services.auth_service.db_conn") as mock_db:
        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(
                token=token, password=password, confirm_password=confirm_password
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Reset token expired"


@pytest.mark.asyncio
async def test_reset_password_token_version_increment():
    """Test that token_version is properly incremented"""
    token = "valid_token"
    password = "new_password123"
    confirm_password = "new_password123"

    mock_user = {
        "id": "user_123",
        "email": "test@example.com",
        "reset_token": token,
        "reset_token_expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "token_version": 5,
    }

    updated_user = {
        "id": "user_123",
        "password_hash": "new_hashed_password",
        "token_version": 6,
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )
        mock_db.users_collection.update_one = AsyncMock()

        await reset_password(
            token=token, password=password, confirm_password=confirm_password
        )

        # Verify token_version is incremented
        update_call = mock_db.users_collection.find_one_and_update.call_args[0][1]
        assert update_call["$inc"]["token_version"] == 1


@pytest.mark.asyncio
async def test_reset_password_cleanup_token_fields():
    """Test that reset token fields are properly cleared"""
    token = "valid_token"
    password = "new_password123"
    confirm_password = "new_password123"

    mock_user = {
        "id": "user_123",
        "email": "test@example.com",
        "reset_token": token,
        "reset_token_expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "token_version": 0,
    }

    updated_user = {
        "id": "user_123",
        "password_hash": "new_hashed_password",
        "token_version": 1,
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )
        mock_db.users_collection.update_one = AsyncMock()

        await reset_password(
            token=token, password=password, confirm_password=confirm_password
        )

        # Verify reset token fields are set to None
        cleanup_call = mock_db.users_collection.update_one.call_args[0][1]
        assert cleanup_call["$set"]["reset_token"] is None
        assert cleanup_call["$set"]["reset_token_expires_at"] is None


@pytest.mark.asyncio
async def test_reset_password_database_update_error():
    """Test handling of database update errors"""
    token = "valid_token"
    password = "new_password123"
    confirm_password = "new_password123"

    mock_user = {
        "id": "user_123",
        "email": "test@example.com",
        "reset_token": token,
        "reset_token_expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "token_version": 0,
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            side_effect=Exception("Database update failed")
        )

        with pytest.raises(Exception, match="Database update failed"):
            await reset_password(
                token=token, password=password, confirm_password=confirm_password
            )


@pytest.mark.asyncio
async def test_reset_password_cleanup_error():
    """Test handling of cleanup operation errors"""
    token = "valid_token"
    password = "new_password123"
    confirm_password = "new_password123"

    mock_user = {
        "id": "user_123",
        "email": "test@example.com",
        "reset_token": token,
        "reset_token_expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "token_version": 0,
    }

    updated_user = {
        "id": "user_123",
        "password_hash": "new_hashed_password",
        "token_version": 1,
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.hash_password", return_value="new_hashed_password"
    ):

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        mock_db.users_collection.find_one_and_update = AsyncMock(
            return_value=updated_user
        )
        mock_db.users_collection.update_one = AsyncMock(
            side_effect=Exception("Cleanup operation failed")
        )

        with pytest.raises(Exception, match="Cleanup operation failed"):
            await reset_password(
                token=token, password=password, confirm_password=confirm_password
            )

        # Password should still be updated before cleanup fails
        mock_db.users_collection.find_one_and_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_reset_password_exactly_expired():
    """Test password reset at exact expiry moment"""
    token = "valid_token"
    password = "new_password123"
    confirm_password = "new_password123"

    # Token expires exactly now
    current_time = datetime.now(timezone.utc)

    mock_user = {
        "id": "user_123",
        "email": "test@example.com",
        "reset_token": token,
        "reset_token_expires_at": current_time,
    }

    with patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.datetime"
    ) as mock_datetime:

        mock_datetime.now.return_value = current_time
        mock_datetime.fromisoformat = datetime.fromisoformat

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(
                token=token, password=password, confirm_password=confirm_password
            )

        # Should fail as token is not valid anymore (< check, not <=)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Reset token expired"


@pytest.mark.asyncio
async def test_refresh_access_token_success():
    """Test successful token refresh with valid refresh token"""
    user_id = "user_123"
    token_version = 1
    old_refresh_token = "old_refresh_token_abc"

    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = old_refresh_token
    mock_response = MagicMock(spec=Response)

    mock_payload = {"sub": user_id, "type": "refresh", "token_version": token_version}

    mock_user = {
        "id": user_id,
        "email": "test@example.com",
        "token_version": token_version,
    }

    with patch(
        "services.auth_service.jwt.decode", return_value=mock_payload
    ) as mock_decode, patch("services.auth_service.db_conn") as mock_db, patch(
        "services.auth_service.create_access_token", return_value="new_access_token"
    ) as mock_create_access, patch(
        "services.auth_service.create_refresh_token", return_value="new_refresh_token"
    ) as mock_create_refresh, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        # Call function
        result = await refresh_access_token(mock_request, mock_response)

        # Verify refresh token was retrieved from cookies
        mock_request.cookies.get.assert_called_once_with("refresh_token")

        # Verify JWT decode
        mock_decode.assert_called_once_with(
            old_refresh_token, "refresh_secret", algorithms=["HS256"]
        )

        # Verify user lookup
        mock_db.users_collection.find_one.assert_awaited_once_with({"id": user_id})

        # Verify new tokens created with correct version
        mock_create_access.assert_called_once_with(user_id, token_version)
        mock_create_refresh.assert_called_once_with(user_id, token_version)

        # Verify cookies set
        assert mock_response.set_cookie.call_count == 2

        access_cookie_call = mock_response.set_cookie.call_args_list[0]
        assert access_cookie_call[1]["key"] == "access_token"
        assert access_cookie_call[1]["value"] == "new_access_token"
        assert access_cookie_call[1]["httponly"] is True
        assert access_cookie_call[1]["secure"] is True
        assert access_cookie_call[1]["samesite"] == "none"
        assert access_cookie_call[1]["max_age"] == 15 * 60

        refresh_cookie_call = mock_response.set_cookie.call_args_list[1]
        assert refresh_cookie_call[1]["key"] == "refresh_token"
        assert refresh_cookie_call[1]["value"] == "new_refresh_token"
        assert refresh_cookie_call[1]["httponly"] is True
        assert refresh_cookie_call[1]["secure"] is True
        assert refresh_cookie_call[1]["samesite"] == "none"
        assert refresh_cookie_call[1]["max_age"] == 7 * 24 * 60 * 60

        # Verify response
        assert result == {"accessToken": "new_access_token"}


@pytest.mark.asyncio
async def test_refresh_access_token_missing_cookie():
    """Test refresh fails when refresh token cookie is missing"""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = None
    mock_response = MagicMock(spec=Response)

    with pytest.raises(HTTPException) as exc_info:
        await refresh_access_token(mock_request, mock_response)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Refresh token missing"


@pytest.mark.asyncio
async def test_refresh_access_token_expired():
    """Test refresh fails when refresh token is expired"""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = "expired_refresh_token"
    mock_response = MagicMock(spec=Response)

    with patch(
        "services.auth_service.jwt.decode",
        side_effect=ExpiredSignatureError("Token expired"),
    ), patch("services.auth_service.settings") as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"

        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token(mock_request, mock_response)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Refresh token expired"


@pytest.mark.asyncio
async def test_refresh_access_token_invalid_token():
    """Test refresh fails with invalid JWT token"""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = "invalid_token"
    mock_response = MagicMock(spec=Response)

    with patch(
        "services.auth_service.jwt.decode", side_effect=JWTError("Invalid token")
    ), patch("services.auth_service.settings") as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"

        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token(mock_request, mock_response)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid refresh token"


@pytest.mark.asyncio
async def test_refresh_access_token_wrong_type():
    """Test refresh fails when token type is not 'refresh'"""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = "access_token_instead"
    mock_response = MagicMock(spec=Response)

    mock_payload = {
        "sub": "user_123",
        "type": "access",  # Wrong type
    }

    with patch("services.auth_service.jwt.decode", return_value=mock_payload), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"

        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token(mock_request, mock_response)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token type"


@pytest.mark.asyncio
async def test_refresh_access_token_missing_sub():
    """Test refresh fails when 'sub' (user_id) is missing from payload"""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = "refresh_token"
    mock_response = MagicMock(spec=Response)

    mock_payload = {
        "type": "refresh",
        # Missing 'sub'
    }

    with patch("services.auth_service.jwt.decode", return_value=mock_payload), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"

        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token(mock_request, mock_response)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid refresh token payload"


@pytest.mark.asyncio
async def test_refresh_access_token_null_sub():
    """Test refresh fails when 'sub' is None"""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = "refresh_token"
    mock_response = MagicMock(spec=Response)

    mock_payload = {"sub": None, "type": "refresh"}

    with patch("services.auth_service.jwt.decode", return_value=mock_payload), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"

        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token(mock_request, mock_response)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid refresh token payload"


@pytest.mark.asyncio
async def test_refresh_access_token_user_not_found():
    """Test refresh fails when user doesn't exist in database"""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = "refresh_token"
    mock_response = MagicMock(spec=Response)

    mock_payload = {"sub": "nonexistent_user", "type": "refresh"}

    with patch("services.auth_service.jwt.decode", return_value=mock_payload), patch(
        "services.auth_service.db_conn"
    ) as mock_db, patch("services.auth_service.settings") as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"

        mock_db.users_collection.find_one = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token(mock_request, mock_response)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_refresh_access_token_default_token_version():
    """Test refresh uses default token_version of 0 when not present"""
    user_id = "user_123"

    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = "refresh_token"
    mock_response = MagicMock(spec=Response)

    mock_payload = {"sub": user_id, "type": "refresh"}

    mock_user = {
        "id": user_id,
        "email": "test@example.com",
        # No token_version field
    }

    with patch("services.auth_service.jwt.decode", return_value=mock_payload), patch(
        "services.auth_service.db_conn"
    ) as mock_db, patch(
        "services.auth_service.create_access_token"
    ) as mock_create_access, patch(
        "services.auth_service.create_refresh_token"
    ) as mock_create_refresh, patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        await refresh_access_token(mock_request, mock_response)

        # Should use default token_version of 0
        mock_create_access.assert_called_once_with(user_id, 0)
        mock_create_refresh.assert_called_once_with(user_id, 0)


@pytest.mark.asyncio
async def test_refresh_access_token_database_error():
    """Test refresh handles database errors"""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = "refresh_token"
    mock_response = MagicMock(spec=Response)

    mock_payload = {"sub": "user_123", "type": "refresh"}

    with patch("services.auth_service.jwt.decode", return_value=mock_payload), patch(
        "services.auth_service.db_conn"
    ) as mock_db, patch("services.auth_service.settings") as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"

        mock_db.users_collection.find_one = AsyncMock(
            side_effect=Exception("Database connection error")
        )

        with pytest.raises(Exception, match="Database connection error"):
            await refresh_access_token(mock_request, mock_response)


@pytest.mark.asyncio
async def test_refresh_access_token_token_creation_error():
    """Test refresh handles token creation errors"""
    user_id = "user_123"

    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = "refresh_token"
    mock_response = MagicMock(spec=Response)

    mock_payload = {"sub": user_id, "type": "refresh"}

    mock_user = {"id": user_id, "email": "test@example.com", "token_version": 0}

    with patch("services.auth_service.jwt.decode", return_value=mock_payload), patch(
        "services.auth_service.db_conn"
    ) as mock_db, patch(
        "services.auth_service.create_access_token",
        side_effect=Exception("Token creation failed"),
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        with pytest.raises(Exception, match="Token creation failed"):
            await refresh_access_token(mock_request, mock_response)


@pytest.mark.asyncio
async def test_refresh_access_token_cookie_security_settings():
    """Test that cookies are set with correct security settings"""
    user_id = "user_123"

    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = "refresh_token"
    mock_response = MagicMock(spec=Response)

    mock_payload = {"sub": user_id, "type": "refresh"}

    mock_user = {"id": user_id, "email": "test@example.com", "token_version": 0}

    with patch("services.auth_service.jwt.decode", return_value=mock_payload), patch(
        "services.auth_service.db_conn"
    ) as mock_db, patch(
        "services.auth_service.create_access_token", return_value="access_token"
    ), patch(
        "services.auth_service.create_refresh_token", return_value="refresh_token"
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 14

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        await refresh_access_token(mock_request, mock_response)

        # Verify both cookies have correct security settings
        for call in mock_response.set_cookie.call_args_list:
            kwargs = call[1]
            assert kwargs["httponly"] is True, "Cookie should be httponly"
            assert kwargs["secure"] is True, "Cookie should be secure"
            assert kwargs["samesite"] == "none", "Cookie should have samesite=none"


@pytest.mark.asyncio
async def test_refresh_access_token_response_format():
    """Test that response contains accessToken"""
    user_id = "user_123"
    new_access = "new_access_token_xyz"

    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = "refresh_token"
    mock_response = MagicMock(spec=Response)

    mock_payload = {"sub": user_id, "type": "refresh"}

    mock_user = {"id": user_id, "email": "test@example.com", "token_version": 0}

    with patch("services.auth_service.jwt.decode", return_value=mock_payload), patch(
        "services.auth_service.db_conn"
    ) as mock_db, patch(
        "services.auth_service.create_access_token", return_value=new_access
    ), patch(
        "services.auth_service.create_refresh_token", return_value="new_refresh"
    ), patch(
        "services.auth_service.settings"
    ) as mock_settings:

        mock_settings.REFRESH_SECRET_KEY = "refresh_secret"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)

        result = await refresh_access_token(mock_request, mock_response)

        assert "accessToken" in result
        assert result["accessToken"] == new_access


@pytest.mark.asyncio
async def test_refresh_access_token_empty_cookie():
    """Test refresh fails when refresh token cookie is empty string"""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies.get.return_value = ""
    mock_response = MagicMock(spec=Response)

    with pytest.raises(HTTPException) as exc_info:
        await refresh_access_token(mock_request, mock_response)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Refresh token missing"


@pytest.mark.asyncio
async def test_logout_user_deletes_cookies():
    # Arrange
    response = MagicMock()
    response.delete_cookie = MagicMock()

    # Act
    await logout_user(response)

    # Assert
    response.delete_cookie.assert_any_call("access_token")
    response.delete_cookie.assert_any_call("refresh_token")
    assert response.delete_cookie.call_count == 2


# Service function tests
@pytest.mark.asyncio
async def test_generate_otp_token_success():
    """Test successful OTP token generation"""
    user_id = "user123"
    email = "user@example.com"
    new_email = "newemail@example.com"

    mock_user = {"id": user_id, "email": email, "name": "Test User"}

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = 10

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.secrets.token_urlsafe", return_value="mock_token_123"
    ):

        result = await generate_otp_token(user_id, email, new_email)

        assert result["otp_token"] == "mock_token_123"
        assert "expires_at" in result
        assert isinstance(result["expires_at"], datetime)

        # Verify user lookup
        mock_db_conn.users_collection.find_one.assert_called_once_with({"id": user_id})

        # Verify token insertion
        mock_db_conn.otp_tokens_collection.insert_one.assert_called_once()
        inserted_doc = mock_db_conn.otp_tokens_collection.insert_one.call_args[0][0]

        assert inserted_doc["user_id"] == user_id
        assert inserted_doc["email"] == email
        assert inserted_doc["new_email"] == new_email
        assert inserted_doc["token"] == "mock_token_123"
        assert inserted_doc["resend_count"] == 0
        assert "created_at" in inserted_doc
        assert "expires_at" in inserted_doc


@pytest.mark.asyncio
async def test_generate_otp_token_user_not_found():
    """Test OTP token generation when user doesn't exist"""
    user_id = "nonexistent_user"
    email = "user@example.com"
    new_email = "newemail@example.com"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)

    with patch("services.auth_service.db_conn", mock_db_conn):

        with pytest.raises(HTTPException) as exc_info:
            await generate_otp_token(user_id, email, new_email)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in str(exc_info.value.detail)

        # Verify user lookup was attempted
        mock_db_conn.users_collection.find_one.assert_called_once_with({"id": user_id})


@pytest.mark.asyncio
async def test_generate_otp_token_token_format():
    """Test that generated token has correct format"""
    user_id = "user123"
    email = "user@example.com"
    new_email = "newemail@example.com"

    mock_user = {"id": user_id, "email": email}

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = 10

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.secrets.token_urlsafe") as mock_token:

        mock_token.return_value = "abcdef123456"

        result = await generate_otp_token(user_id, email, new_email)

        mock_token.assert_called_once_with(32)
        assert result["otp_token"] == "abcdef123456"


@pytest.mark.asyncio
async def test_generate_otp_token_expiry_calculation():
    """Test that token expiry is calculated correctly"""
    user_id = "user123"
    email = "user@example.com"
    new_email = "newemail@example.com"
    expire_minutes = 15

    mock_user = {"id": user_id, "email": email}

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = expire_minutes

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.secrets.token_urlsafe", return_value="token123"):

        before_time = datetime.now(timezone.utc)

        result = await generate_otp_token(user_id, email, new_email)

        after_time = datetime.now(timezone.utc)

        expires_at = result["expires_at"]
        expected_min = before_time + timedelta(minutes=expire_minutes)
        expected_max = after_time + timedelta(minutes=expire_minutes)

        assert expected_min <= expires_at <= expected_max


@pytest.mark.asyncio
async def test_generate_otp_token_initial_resend_count():
    """Test that resend_count is initialized to 0"""
    user_id = "user123"
    email = "user@example.com"
    new_email = "newemail@example.com"

    mock_user = {"id": user_id, "email": email}

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = 10

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.secrets.token_urlsafe", return_value="token123"):

        await generate_otp_token(user_id, email, new_email)

        inserted_doc = mock_db_conn.otp_tokens_collection.insert_one.call_args[0][0]
        assert inserted_doc["resend_count"] == 0


@pytest.mark.asyncio
async def test_generate_otp_token_database_error():
    """Test handling of database errors during insertion"""
    user_id = "user123"
    email = "user@example.com"
    new_email = "newemail@example.com"

    mock_user = {"id": user_id, "email": email}

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=mock_user)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock(
        side_effect=Exception("Database connection failed")
    )

    mock_settings = MagicMock()
    mock_settings.OTP_EXPIRE_MINUTES = 10

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.secrets.token_urlsafe", return_value="token123"):

        with pytest.raises(Exception) as exc_info:
            await generate_otp_token(user_id, email, new_email)

        assert "Database connection failed" in str(exc_info.value)


# Service function tests
@pytest.mark.asyncio
async def test_resend_email_change_otp_success():
    """Test successful OTP resend"""
    user_id = "user123"

    token_doc = {
        "_id": "token_id_123",
        "user_id": user_id,
        "email": "user@example.com",
        "new_email": "newemail@example.com",
        "token": "mock_token",
        "resend_count": 0,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "created_at": datetime.now(timezone.utc),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=token_doc)
    mock_db_conn.otp_tokens_collection.update_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.send_otp", new_callable=AsyncMock) as mock_send_otp:

        result = await resend_email_change_otp(user_id)

        assert result["message"] == "OTP resent successfully"
        assert result["resend_count"] == 1

        # Verify token lookup
        mock_db_conn.otp_tokens_collection.find_one.assert_called_once_with(
            {"user_id": user_id, "expires_at": {"$gt": ANY}}, sort=[("created_at", -1)]
        )

        # Verify resend_count update
        mock_db_conn.otp_tokens_collection.update_one.assert_called_once_with(
            {"_id": "token_id_123"}, {"$set": {"resend_count": 1}}
        )

        # Verify OTP was sent
        mock_send_otp.assert_called_once_with(
            "newemail@example.com",
            user_id=user_id,
            email_template="email_change.html",
            purpose="email_change",
        )


@pytest.mark.asyncio
async def test_resend_email_change_otp_token_not_found():
    """Test OTP resend when token not found"""
    user_id = "user123"

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=None)

    with patch("services.auth_service.db_conn", mock_db_conn):

        with pytest.raises(HTTPException) as exc_info:
            await resend_email_change_otp(user_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "OTP token not found or expired" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_resend_email_change_otp_token_expired():
    """Test OTP resend when token is expired"""
    user_id = "user123"

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=None)

    with patch("services.auth_service.db_conn", mock_db_conn):

        with pytest.raises(HTTPException) as exc_info:
            await resend_email_change_otp(user_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Please restart email change process" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_resend_email_change_otp_limit_exceeded():
    """Test OTP resend when limit is exceeded"""
    user_id = "user123"

    token_doc = {
        "_id": "token_id_123",
        "user_id": user_id,
        "email": "user@example.com",
        "new_email": "newemail@example.com",
        "token": "mock_token",
        "resend_count": 3,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "created_at": datetime.now(timezone.utc),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=token_doc)
    mock_db_conn.otp_tokens_collection.delete_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ):

        with pytest.raises(HTTPException) as exc_info:
            await resend_email_change_otp(user_id)

        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Resend OTP limit exceeded" in str(exc_info.value.detail)

        # Verify token was deleted
        mock_db_conn.otp_tokens_collection.delete_one.assert_called_once_with(
            {"_id": "token_id_123"}
        )


@pytest.mark.asyncio
async def test_resend_email_change_otp_increments_count():
    """Test that resend_count is properly incremented"""
    user_id = "user123"

    token_doc = {
        "_id": "token_id_123",
        "user_id": user_id,
        "email": "user@example.com",
        "new_email": "newemail@example.com",
        "token": "mock_token",
        "resend_count": 2,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "created_at": datetime.now(timezone.utc),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=token_doc)
    mock_db_conn.otp_tokens_collection.update_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 5

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.send_otp", new_callable=AsyncMock):

        result = await resend_email_change_otp(user_id)

        assert result["resend_count"] == 3

        mock_db_conn.otp_tokens_collection.update_one.assert_called_once_with(
            {"_id": "token_id_123"}, {"$set": {"resend_count": 3}}
        )


@pytest.mark.asyncio
async def test_resend_email_change_otp_missing_resend_count():
    """Test OTP resend when resend_count field is missing"""
    user_id = "user123"

    token_doc = {
        "_id": "token_id_123",
        "user_id": user_id,
        "email": "user@example.com",
        "new_email": "newemail@example.com",
        "token": "mock_token",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "created_at": datetime.now(timezone.utc),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=token_doc)
    mock_db_conn.otp_tokens_collection.update_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.send_otp", new_callable=AsyncMock):

        result = await resend_email_change_otp(user_id)

        assert result["resend_count"] == 1


@pytest.mark.asyncio
async def test_resend_email_change_otp_sends_to_new_email():
    """Test that OTP is sent to new_email"""
    user_id = "user123"
    new_email = "newemail@example.com"

    token_doc = {
        "_id": "token_id_123",
        "user_id": user_id,
        "email": "user@example.com",
        "new_email": new_email,
        "token": "mock_token",
        "resend_count": 0,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "created_at": datetime.now(timezone.utc),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=token_doc)
    mock_db_conn.otp_tokens_collection.update_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.send_otp", new_callable=AsyncMock) as mock_send_otp:

        await resend_email_change_otp(user_id)

        mock_send_otp.assert_called_once_with(
            new_email,
            user_id=user_id,
            email_template="email_change.html",
            purpose="email_change",
        )


@pytest.mark.asyncio
async def test_resend_email_change_otp_at_limit_boundary():
    """Test OTP resend exactly at the limit"""
    user_id = "user123"

    token_doc = {
        "_id": "token_id_123",
        "user_id": user_id,
        "email": "user@example.com",
        "new_email": "newemail@example.com",
        "token": "mock_token",
        "resend_count": 2,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "created_at": datetime.now(timezone.utc),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=token_doc)
    mock_db_conn.otp_tokens_collection.update_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.send_otp", new_callable=AsyncMock):

        result = await resend_email_change_otp(user_id)

        assert result["resend_count"] == 3
        assert result["message"] == "OTP resent successfully"


@pytest.mark.asyncio
async def test_resend_email_change_otp_send_otp_failure():
    """Test handling of send_otp failure"""
    user_id = "user123"

    token_doc = {
        "_id": "token_id_123",
        "user_id": user_id,
        "email": "user@example.com",
        "new_email": "newemail@example.com",
        "token": "mock_token",
        "resend_count": 0,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "created_at": datetime.now(timezone.utc),
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=token_doc)
    mock_db_conn.otp_tokens_collection.update_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.send_otp",
        new_callable=AsyncMock,
        side_effect=Exception("Email service unavailable"),
    ):

        with pytest.raises(Exception) as exc_info:
            await resend_email_change_otp(user_id)

        assert "Email service unavailable" in str(exc_info.value)


# Service function tests
@pytest.mark.asyncio
async def test_request_signup_otp_success():
    """Test successful signup OTP request"""
    email = "newuser@example.com"
    first_name = "John"
    last_name = "Doe"
    password = "password123"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_TOKEN_EXPIRE_MINUTES = 10
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.secrets.token_urlsafe",
        side_effect=["temp_token_123", "user_id_123"],
    ), patch(
        "services.auth_service.hash_password", return_value="hashed_password"
    ), patch(
        "services.auth_service.send_otp", new_callable=AsyncMock
    ):

        result = await request_signup_otp(email, first_name, last_name, password)

        assert result["message"] == "Verification code sent to your email"
        assert result["email"] == email

        # Verify user existence check
        mock_db_conn.users_collection.find_one.assert_called_once_with({"email": email})

        # Verify existing OTP token check
        mock_db_conn.otp_tokens_collection.find_one.assert_called_once_with(
            {"email": email, "otp_type": "signup"}
        )

        # Verify OTP token insertion
        mock_db_conn.otp_tokens_collection.insert_one.assert_called_once()
        inserted_doc = mock_db_conn.otp_tokens_collection.insert_one.call_args[0][0]

        assert inserted_doc["email"] == email
        assert inserted_doc["otp_type"] == "signup"
        assert inserted_doc["resend_count"] == 0
        assert inserted_doc["pending_data"]["first_name"] == first_name
        assert inserted_doc["pending_data"]["last_name"] == last_name
        assert inserted_doc["pending_data"]["password_hash"] == "hashed_password"


@pytest.mark.asyncio
async def test_request_signup_otp_user_already_exists():
    """Test signup OTP request when user already exists"""
    email = "existing@example.com"
    first_name = "John"
    last_name = "Doe"
    password = "password123"

    existing_user = {
        "id": "user123",
        "email": email,
        "first_name": "John",
        "last_name": "Doe",
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=existing_user)

    with patch("services.auth_service.db_conn", mock_db_conn):

        with pytest.raises(HTTPException) as exc_info:
            await request_signup_otp(email, first_name, last_name, password)

        assert exc_info.value.status_code == 400
        assert "User with this email already exists" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_request_signup_otp_deletes_existing_token():
    """Test that existing OTP token is deleted before creating new one"""
    email = "user@example.com"
    first_name = "John"
    last_name = "Doe"
    password = "password123"

    existing_otp_token = {
        "_id": "old_token_id",
        "email": email,
        "otp_type": "signup",
        "resend_count": 1,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(
        return_value=existing_otp_token
    )
    mock_db_conn.otp_tokens_collection.delete_one = AsyncMock()
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_TOKEN_EXPIRE_MINUTES = 10
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.secrets.token_urlsafe", return_value="token_123"
    ), patch(
        "services.auth_service.hash_password", return_value="hashed_password"
    ), patch(
        "services.auth_service.send_otp", new_callable=AsyncMock
    ):

        await request_signup_otp(email, first_name, last_name, password)

        # Verify old token was deleted
        mock_db_conn.otp_tokens_collection.delete_one.assert_called_once_with(
            {"_id": "old_token_id"}
        )


@pytest.mark.asyncio
async def test_request_signup_otp_resend_limit_exceeded():
    """Test signup OTP request when resend limit exceeded"""
    email = "user@example.com"
    first_name = "John"
    last_name = "Doe"
    password = "password123"

    existing_otp_token = {
        "_id": "token_id",
        "email": email,
        "otp_type": "signup",
        "resend_count": 3,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(
        return_value=existing_otp_token
    )

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ):

        with pytest.raises(HTTPException) as exc_info:
            await request_signup_otp(email, first_name, last_name, password)

        assert exc_info.value.status_code == 429
        assert "Resend OTP limit exceeded" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_request_signup_otp_password_hashing():
    """Test that password is properly hashed"""
    email = "user@example.com"
    first_name = "John"
    last_name = "Doe"
    password = "password123"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_TOKEN_EXPIRE_MINUTES = 10
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.secrets.token_urlsafe", return_value="token_123"
    ), patch(
        "services.auth_service.hash_password", return_value="hashed_password_xyz"
    ) as mock_hash, patch(
        "services.auth_service.send_otp", new_callable=AsyncMock
    ):

        await request_signup_otp(email, first_name, last_name, password)

        # Verify password was hashed
        mock_hash.assert_called_once_with(password)

        # Verify hashed password stored in pending_data
        inserted_doc = mock_db_conn.otp_tokens_collection.insert_one.call_args[0][0]
        assert inserted_doc["pending_data"]["password_hash"] == "hashed_password_xyz"


@pytest.mark.asyncio
async def test_request_signup_otp_token_expiry():
    """Test that token expiry is set correctly"""
    email = "user@example.com"
    first_name = "John"
    last_name = "Doe"
    password = "password123"
    expire_minutes = 15

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_TOKEN_EXPIRE_MINUTES = expire_minutes
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.secrets.token_urlsafe", return_value="token_123"
    ), patch(
        "services.auth_service.hash_password", return_value="hashed_password"
    ), patch(
        "services.auth_service.send_otp", new_callable=AsyncMock
    ):

        before_time = datetime.now(timezone.utc)

        await request_signup_otp(email, first_name, last_name, password)

        after_time = datetime.now(timezone.utc)

        inserted_doc = mock_db_conn.otp_tokens_collection.insert_one.call_args[0][0]
        expires_at = inserted_doc["expires_at"]

        expected_min = before_time + timedelta(minutes=expire_minutes)
        expected_max = after_time + timedelta(minutes=expire_minutes)

        assert expected_min <= expires_at <= expected_max


@pytest.mark.asyncio
async def test_request_signup_otp_sends_email():
    """Test that OTP email is sent correctly"""
    email = "user@example.com"
    first_name = "John"
    last_name = "Doe"
    password = "password123"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_TOKEN_EXPIRE_MINUTES = 10
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.secrets.token_urlsafe",
        side_effect=["temp_token", "user_id_123"],
    ), patch(
        "services.auth_service.hash_password", return_value="hashed_password"
    ), patch(
        "services.auth_service.send_otp", new_callable=AsyncMock
    ) as mock_send_otp:

        await request_signup_otp(email, first_name, last_name, password)

        # Verify send_otp was called with correct parameters
        mock_send_otp.assert_called_once_with(
            email=email,
            user_id="user_id_123",
            email_template="email_signup.html",
            purpose="signup",
        )


@pytest.mark.asyncio
async def test_request_signup_otp_email_failure_rollback():
    """Test that OTP token is deleted if email sending fails"""
    email = "user@example.com"
    first_name = "John"
    last_name = "Doe"
    password = "password123"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()
    mock_db_conn.otp_tokens_collection.delete_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_TOKEN_EXPIRE_MINUTES = 10
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.secrets.token_urlsafe", return_value="token_123"
    ), patch(
        "services.auth_service.hash_password", return_value="hashed_password"
    ), patch(
        "services.auth_service.send_otp",
        new_callable=AsyncMock,
        side_effect=Exception("SMTP connection failed"),
    ):

        with pytest.raises(HTTPException) as exc_info:
            await request_signup_otp(email, first_name, last_name, password)

        assert exc_info.value.status_code == 500
        assert "Failed to send verification email" in str(exc_info.value.detail)

        # Verify rollback: OTP token was deleted
        mock_db_conn.otp_tokens_collection.delete_one.assert_called_once_with(
            {"email": email, "otp_type": "signup"}
        )


@pytest.mark.asyncio
async def test_request_signup_otp_stores_pending_data():
    """Test that all pending signup data is stored correctly"""
    email = "user@example.com"
    first_name = "Jane"
    last_name = "Smith"
    password = "securepass456"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_TOKEN_EXPIRE_MINUTES = 10
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.secrets.token_urlsafe", return_value="token_123"
    ), patch(
        "services.auth_service.hash_password", return_value="hashed_password"
    ), patch(
        "services.auth_service.send_otp", new_callable=AsyncMock
    ):

        await request_signup_otp(email, first_name, last_name, password)

        inserted_doc = mock_db_conn.otp_tokens_collection.insert_one.call_args[0][0]
        pending_data = inserted_doc["pending_data"]

        assert pending_data["first_name"] == first_name
        assert pending_data["last_name"] == last_name
        assert pending_data["password_hash"] == "hashed_password"
        assert inserted_doc["email"] == email
        assert inserted_doc["new_email"] is None


@pytest.mark.asyncio
async def test_request_signup_otp_initial_resend_count():
    """Test that resend_count is initialized to 0"""
    email = "user@example.com"
    first_name = "John"
    last_name = "Doe"
    password = "password123"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_TOKEN_EXPIRE_MINUTES = 10
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.secrets.token_urlsafe", return_value="token_123"
    ), patch(
        "services.auth_service.hash_password", return_value="hashed_password"
    ), patch(
        "services.auth_service.send_otp", new_callable=AsyncMock
    ):

        await request_signup_otp(email, first_name, last_name, password)

        inserted_doc = mock_db_conn.otp_tokens_collection.insert_one.call_args[0][0]
        assert inserted_doc["resend_count"] == 0


@pytest.mark.asyncio
async def test_request_signup_otp_generates_unique_tokens():
    """Test that unique tokens are generated"""
    email = "user@example.com"
    first_name = "John"
    last_name = "Doe"
    password = "password123"

    mock_db_conn = MagicMock()
    mock_db_conn.users_collection = AsyncMock()
    mock_db_conn.users_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=None)
    mock_db_conn.otp_tokens_collection.insert_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.OTP_TOKEN_EXPIRE_MINUTES = 10
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.secrets.token_urlsafe",
        side_effect=["temp_token_abc", "user_id_xyz"],
    ), patch(
        "services.auth_service.hash_password", return_value="hashed_password"
    ), patch(
        "services.auth_service.send_otp", new_callable=AsyncMock
    ):

        await request_signup_otp(email, first_name, last_name, password)

        inserted_doc = mock_db_conn.otp_tokens_collection.insert_one.call_args[0][0]
        assert inserted_doc["token"] == "temp_token_abc"
        assert inserted_doc["user_id"] == "user_id_xyz"


@pytest.mark.asyncio
async def test_resend_signup_otp_success():
    """Test successful OTP resend with incremented count"""
    email = "user@example.com"
    user_id = "user_123"

    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "user_id": user_id,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        "resend_count": 0,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
    mock_db_conn.otp_tokens_collection.update_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.send_otp", new_callable=AsyncMock) as mock_send_otp:

        result = await resend_signup_otp(email)

        assert result["message"] == "Verification code resent successfully"
        assert result["resend_count"] == 1

        mock_db_conn.otp_tokens_collection.update_one.assert_called_once_with(
            {"_id": "token_id_123"}, {"$set": {"resend_count": 1}}
        )

        mock_send_otp.assert_called_once_with(
            email=email,
            user_id=user_id,
            email_template="email_signup.html",
            purpose="signup",
        )


@pytest.mark.asyncio
async def test_resend_signup_otp_not_found():
    """Test error when OTP token doesn't exist"""
    email = "user@example.com"

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=None)

    with patch("services.auth_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await resend_signup_otp(email)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "OTP token not found or expired"


@pytest.mark.asyncio
async def test_resend_signup_otp_expired():
    """Test error when OTP token has expired"""
    email = "user@example.com"

    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "user_id": "user_123",
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) - timedelta(minutes=5),
        "resend_count": 0,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
    mock_db_conn.otp_tokens_collection.delete_one = AsyncMock()

    with patch("services.auth_service.db_conn", mock_db_conn):
        with pytest.raises(HTTPException) as exc_info:
            await resend_signup_otp(email)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "OTP has expired. Please restart signup process"

        mock_db_conn.otp_tokens_collection.delete_one.assert_called_once_with(
            {"_id": "token_id_123"}
        )


@pytest.mark.asyncio
async def test_resend_signup_otp_limit_reached():
    """Test error when resend limit is reached"""
    email = "user@example.com"

    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "user_id": "user_123",
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        "resend_count": 3,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
    mock_db_conn.otp_tokens_collection.delete_one = AsyncMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.otps_collection.delete_many = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ):
        with pytest.raises(HTTPException) as exc_info:
            await resend_signup_otp(email)

        assert exc_info.value.status_code == 429
        assert (
            exc_info.value.detail
            == "Resend limit reached. Please restart signup process"
        )

        mock_db_conn.otp_tokens_collection.delete_one.assert_called_once_with(
            {"_id": "token_id_123"}
        )
        mock_db_conn.otps_collection.delete_many.assert_called_once_with(
            {"email": email}
        )


@pytest.mark.asyncio
async def test_resend_signup_otp_at_limit_edge():
    """Test that exactly at limit triggers error"""
    email = "user@example.com"

    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "user_id": "user_123",
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        "resend_count": 5,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
    mock_db_conn.otp_tokens_collection.delete_one = AsyncMock()
    mock_db_conn.otps_collection = AsyncMock()
    mock_db_conn.otps_collection.delete_many = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 5

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ):
        with pytest.raises(HTTPException) as exc_info:
            await resend_signup_otp(email)

        assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_resend_signup_otp_missing_resend_count():
    """Test handling when resend_count field is missing (defaults to 0)"""
    email = "user@example.com"
    user_id = "user_123"

    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "user_id": user_id,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        # No resend_count field
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
    mock_db_conn.otp_tokens_collection.update_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.send_otp", new_callable=AsyncMock):

        result = await resend_signup_otp(email)

        assert result["resend_count"] == 1

        mock_db_conn.otp_tokens_collection.update_one.assert_called_once_with(
            {"_id": "token_id_123"}, {"$set": {"resend_count": 1}}
        )


@pytest.mark.asyncio
async def test_resend_signup_otp_send_fails():
    """Test error handling when send_otp fails"""
    email = "user@example.com"

    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "user_id": "user_123",
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        "resend_count": 1,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
    mock_db_conn.otp_tokens_collection.update_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 3

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch(
        "services.auth_service.send_otp",
        new_callable=AsyncMock,
        side_effect=Exception("Email service error"),
    ):

        with pytest.raises(HTTPException) as exc_info:
            await resend_signup_otp(email)

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Failed to resend verification email"

        # Verify count was still incremented before failure
        mock_db_conn.otp_tokens_collection.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_resend_signup_otp_multiple_resends():
    """Test incrementing resend count through multiple resends"""
    email = "user@example.com"
    user_id = "user_123"

    mock_otp_token = {
        "_id": "token_id_123",
        "email": email,
        "user_id": user_id,
        "otp_type": "signup",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        "resend_count": 2,
    }

    mock_db_conn = MagicMock()
    mock_db_conn.otp_tokens_collection = AsyncMock()
    mock_db_conn.otp_tokens_collection.find_one = AsyncMock(return_value=mock_otp_token)
    mock_db_conn.otp_tokens_collection.update_one = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.RESEND_OTP_LIMIT = 5

    with patch("services.auth_service.db_conn", mock_db_conn), patch(
        "services.auth_service.settings", mock_settings
    ), patch("services.auth_service.send_otp", new_callable=AsyncMock):

        result = await resend_signup_otp(email)

        assert result["resend_count"] == 3

        mock_db_conn.otp_tokens_collection.update_one.assert_called_once_with(
            {"_id": "token_id_123"}, {"$set": {"resend_count": 3}}
        )
