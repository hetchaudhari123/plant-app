# Jobs
DELETE_JOB_BY_USER_ID = "/jobs/user/{user_id}"


# ----------------------------
# OTP endpoints
# ----------------------------
DELETE_OTPS_BY_EMAIL = "/otps/{email}"                       # DELETE
GET_OTP_BY_CODE = "/otps/code/{otp_code}"                    # GET
CREATE_OTP = "/otps/"                                         # POST
GET_OTP_BY_EMAIL_AND_CODE = "/otps/verify"                  # GET with params {"email", "otp"}
GET_OTP_BY_EMAIL = "/otps/email"                             # GET with param {"email"}
DELETE_OTPS_BY_USER = "/otps/user/{user_id}"                # DELETE
GET_OTP_FOR_EMAIL_CHANGE = "/otps/email-change"             # GET with params {"user_id", "email", "otp", "purpose"}




# ----------------------------
# User endpoints
# ----------------------------
GET_USER_BY_EMAIL = "/users/email/{email}"               # GET
CREATE_USER = "/users/"                                  # POST
GET_USER_DETAILS = "/users"                     # GET
GET_USER_BY_ID = "/user/{user_id}"                     # GET
UPDATE_USER_PASSWORD = "/users/{user_id}/password"     # PUT
UPDATE_RESET_TOKEN = "/users/{user_id}/reset-token"    # PUT
GET_USER_BY_RESET_TOKEN = "/users/reset-token/{token}" # GET
UPDATE_USER_PROFILE = "/users/{user_id}/profile"       # PUT
DELETE_USER = "/users/{user_id}"                        # DELETE
UPDATE_USER_PROFILE_PIC = "/users/{user_id}/profile-pic" # PUT
UPDATE_FARM_SIZE = "/users/update-farm-size" # PUT
GET_USER_DASHBOARD_DETAILS = "/users/get-dashboard-details" # GET
GET_PRIMARY_CROPS = "/users/primary-crops"
CREATE_OTP_TOKEN = "/otp-token"
ROUTE_RESEND_OTP = "/otp-token/resend-otp"
LOGOUT= "/logout"

#Model
GET_MODEL_PREDICTION  = "/model/predict/{model_name}"  # adjust if different

# Prediction-related
CREATE_PREDICTION = "/predictions/create-prediction"  # POST
DELETE_PREDICTIONS_BY_USER = "/predictions/user/{user_id}"