import { apiConnector } from "./apiconnector";
import { API_ROUTES } from "../config/apiRoutes";

export const sendOtp = async (email: string) => {
  return apiConnector("POST", API_ROUTES.SEND_OTP, { email });
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
  } catch (error: unknown) {
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
  } catch (error: unknown) {
    console.error("Error logging out user:", error);
    throw error;
  }
};



export interface SignupRequestOtpRequest {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
}

export const requestSignupOtp = async (data: SignupRequestOtpRequest) => {
  try {
    const bodyData = {
      email: data.email,
      first_name: data.first_name,
      last_name: data.last_name,
      password: data.password
    };

    const response = await apiConnector(
      "POST",
      `${API_ROUTES.REQUEST_SIGNUP_OTP}`,
      bodyData,
      { "Content-Type": "application/json" }
    );

    return response;
  } catch (error: unknown) {
    console.error("Error requesting signup OTP:", error);
    throw error;
  }
};

export interface VerifySignupOtpRequest {
  email: string;
  otp_code: string;
}

export interface VerifySignupOtpResponse {
  message: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    profile_pic_url: string;
  };
}

export const verifySignupOtp = async (data: VerifySignupOtpRequest): Promise<VerifySignupOtpResponse> => {
  try {
    const bodyData = {
      email: data.email,
      otp_code: data.otp_code
    };

    const response = await apiConnector(
      "POST",
      `${API_ROUTES.VERIFY_SIGNUP_OTP}`,
      bodyData,
      { "Content-Type": "application/json" }
    );

    return response;
  } catch (error: unknown) {
    console.error("Error verifying signup OTP:", error);
    throw error;
  }
};


export interface ResendSignupOtpRequest {
  email: string;
}

export interface ResendSignupOtpResponse {
  message: string;
  resend_count: number;
}

export const resendSignupOtp = async (data: ResendSignupOtpRequest): Promise<ResendSignupOtpResponse> => {
  try {
    const bodyData = {
      email: data.email
    };

    const response = await apiConnector(
      "POST",
      `${API_ROUTES.RESEND_SIGNUP_OTP}`,
      bodyData,
      { "Content-Type": "application/json" }
    );

    return response;
  } catch (error: unknown) {
    console.error("Error resending signup OTP:", error);
    throw error;
  }
};




// Request password reset token
export interface RequestPasswordResetRequest {
  email: string;
}

export const requestPasswordReset = async (email: string) => {
  try {
    const bodyData = { email };
    
    const response = await apiConnector(
      "POST",
      `${API_ROUTES.REQUEST_PASSWORD_RESET}`,
      bodyData,
      { "Content-Type": "application/json" }
    );

    return response;
  } catch (error: unknown) {
    console.error("Error requesting password reset:", error);
    throw error;
  }
};

// Reset password with token
export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirm_password: string;
}

export const resetPassword = async (data: ResetPasswordRequest) => {
  try {
    const bodyData = {
      token: data.token,
      password: data.password,
      confirm_password: data.confirm_password
    };
    const response = await apiConnector(
      "POST",
      `${API_ROUTES.RESET_PASSWORD}`,
      bodyData,
      { "Content-Type": "application/json" }
    );

    return response;
  } catch (error: unknown) {
    console.error("Error resetting password:", error);
    throw error;
  }
};