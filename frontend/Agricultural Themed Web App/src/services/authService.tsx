// src/services/authService.ts
import { apiConnector } from "./apiconnector";
import { API_ROUTES } from "../config/apiRoutes";

// authService.ts
export const sendOtp = async (email: string) => {
  return apiConnector("POST", API_ROUTES.SEND_OTP, { email });
};

export const signup = async (formData: { firstName: string; lastName: string; email: string; password: string; otp: string }) => {
  return apiConnector("POST", API_ROUTES.SIGNUP, formData);
};

export const login = async (email: string, password: string) => {
  return apiConnector("POST", API_ROUTES.LOGIN, { email, password });
};

export const refreshAccessToken = async () => {
  return apiConnector("POST", API_ROUTES.REFRESH_TOKEN);
};

export const logout = async () => {
  return apiConnector("POST", API_ROUTES.LOGOUT);
};