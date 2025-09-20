# app_service/crud_apis/__init__.py

# Import OTP API wrappers
from .otp_api import (
    delete_otps_for_email,
    get_otp_by_code,
    create_otp,
    get_otp_by_email_and_code,
    get_otp_by_email,
    get_otp_for_email_change,
    delete_otps_by_user
)

# Import User API wrappers
from .users_api import (
    get_user_by_email,
    create_user,
    get_user_by_id,
    update_user_password,
    update_reset_token,
    get_user_by_reset_token,
    update_user_profile,
    delete_user,
    update_user_profile_pic
)

# Import Prediction API wrappers
from .predictions_api import delete_predictions_by_user

# Import Job API wrappers
from .jobs_api import delete_jobs_by_user

# Optionally, define __all__ for cleaner wildcard imports
__all__ = [
    # OTP
    "delete_otps_for_email", "get_otp_by_code", "create_otp",
    "get_otp_by_email_and_code", "get_otp_by_email", "get_otp_for_email_change",
    "delete_otps_by_user",
    # User
    "get_user_by_email", "create_user", "get_user_by_id",
    "update_user_password", "update_reset_token", "get_user_by_reset_token",
    "update_user_profile", "delete_user", "update_user_profile_pic",
    # Predictions
    "delete_predictions_by_user",
    # Jobs
    "delete_jobs_by_user"
]
