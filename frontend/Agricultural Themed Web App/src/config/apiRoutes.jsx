export const API_ROUTES = {
  // User-related APIs
  LOGIN: "/auth/login",
  LOGOUT: "/auth/logout",
  REQUEST_SIGNUP_OTP: "/auth/signup/request-otp",
  UPDATE_PROFILE: "/auth/profile",
  SEND_OTP: "/auth/send-otp",
  REFRESH_TOKEN: "/auth/refresh",
  CREATE_OTP_TOKEN: "auth/otp-token",
  RESEND_OTP: "/auth/otp-token/resend-otp",
  CHANGE_PASSWORD: "/auth/change-password",
  LOG_OUT: "/auth/logout",
  VERIFY_SIGNUP_OTP: "/auth/signup/verify-otp",
  RESEND_SIGNUP_OTP: "/auth/signup/resend-otp",
  REQUEST_PASSWORD_RESET: "/auth/reset-password-token",
  RESET_PASSWORD: "/auth/reset-password",


  // Profile
  GET_USER: "profile/user",
  GET_USER_DETAILS: "profile/users",
  GET_USER_DASHBOARD_DETAILS: "profile/users/get-dashboard-details",
  GET_USER_PRIMARY_CROPS: "profile/users/primary-crops",
  UPDATE_USER_NAME: "profile/update-name",
  UPDATE_USER_AVATAR: "profile/update-profile-picture",
  GET_OTP_FOR_EMAIL_CHANGE: "profile/request-email-change",
  VERIFY_EMAIL_UPDATE_OTP: "profile/confirm-email-change",
  UPDATE_USER_FARM_SIZE: "profile/users/update-farm-size",
  DELETE_USER: "profile/delete-account",

  // MODEL
  GET_ALL_MODELS: "model/models",

  // PREDICTION
  CREATE_PREDICTION: "prediction",
  GET_USER_PREDICTIONS: "prediction/get-user-predictions",
  DELETE_PREDICTION: "prediction/delete-prediction"
};
