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

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
  confirm_password: string;
}



export const changePassword = async ({ old_password, new_password, confirm_password }: ChangePasswordRequest) => {
  try {
    const bodyData = { old_password, new_password, confirm_password };
    const response = await apiConnector(
      "POST",
      `${API_ROUTES.CHANGE_PASSWORD}`, // your backend route
      bodyData,
      { "Content-Type": "application/json" }
    );

    return response;
  } catch (error: any) {
    console.error("Error changing password:", error);
    throw error;
  }
};


export const logoutUser = async () => {
  try {
    const response = await apiConnector(
      "POST",
      `${API_ROUTES.LOGOUT}`, // your backend route
      {},
      { "Content-Type": "application/json" }
    );

    return response;
  } catch (error: any) {
    console.error("Error logging out user:", error);
    throw error;
  }
};