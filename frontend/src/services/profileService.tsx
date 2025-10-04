import { apiConnector } from "./apiconnector";
import { API_ROUTES } from "../config/apiRoutes";

export const getUserById = async (userId: string) => {
  try {
    const response = await apiConnector("GET", `${API_ROUTES.GET_USER}/${userId}`);
    return response.data; 
  } catch (error: any) {
    console.error("Error fetching user:", error);
    throw error;
  }
};

export const getUserDetails = async () => {
  try {
    const response = await apiConnector("GET", `${API_ROUTES.GET_USER_DETAILS}`);
    return response.data; 
  } catch (error: any) {
    console.error("Error fetching user:", error);
    throw error;
  }
};

export const getUserPrimaryCrops = async () => {
  try {
    const response = await apiConnector("GET", `${API_ROUTES.GET_USER_PRIMARY_CROPS}`);
    return response;
  } catch (error: any) {
    console.error("Error fetching user's primary crops:", error);
    throw error;
  }
};

export const getUserDashboardMetrics = async () => {
  try {
    const response = await apiConnector("GET", `${API_ROUTES.GET_USER_DASHBOARD_DETAILS}`);
    return response; 
  } catch (error: any) {
    console.error("Error fetching user's dashboard metrics:", error);
    throw error;
  }
};


export const updateUserName = async ({
  firstName,
  lastName
}: {
  firstName: string;
  lastName: string;
}) => {
  try {
    const response = await apiConnector("PUT", `${API_ROUTES.UPDATE_USER_NAME}`,
      {
        first_name: firstName,
        last_name: lastName,
      }
    );
    return response; 
  } catch (error: any) {
    console.error("Error fetching user's name:", error);
    throw error;
  }
};


export const updateUserAvatar = async (file: File) => {
  try {
    const formData = new FormData();
    formData.append("file", file); 
    const response = await apiConnector(
      "PUT",
      `${API_ROUTES.UPDATE_USER_AVATAR}`,
      formData, // bodyData
      { "Content-Type": "multipart/form-data" } // headers
    );

    return response;
  } catch (error: any) {
    console.error("Error updating user's avatar:", error);
    throw error;
  }
};

interface UpdateEmailRequest {
  new_email: string;
  current_password: string;
}

export const requestEmailUpdateOtp = async ({ new_email, current_password }: UpdateEmailRequest) => {
  try {
    const bodyData = { new_email, current_password };

    const response = await apiConnector(
      "POST",
      `${API_ROUTES.GET_OTP_FOR_EMAIL_CHANGE}`,
      bodyData,
      { "Content-Type": "application/json" }
    );

    return response;
  } catch (error: any) {
    console.error("Error sending OTP for email update:", error);
    throw error;
  }
};




interface VerifyOtpRequest {
  otp_code: string;
  new_email: string;
  old_email: string;
}

export const verifyEmailUpdateOtp = async ({ otp_code, new_email, old_email }: VerifyOtpRequest) => {
  try {
    const bodyData = { otp_code: otp_code, new_email, old_email };
    const response = await apiConnector(
      "POST",
      `${API_ROUTES.VERIFY_EMAIL_UPDATE_OTP}`, 
      bodyData,
      { "Content-Type": "application/json" }
    );

    return response;
  } catch (error: any) {
    console.error("Error verifying OTP for email update:", error);
    throw error;
  }
};

export const updateFarmSize = async (farmSize: string) => {
  try {
    const response = await apiConnector(
      "PUT",
      `${API_ROUTES.UPDATE_USER_FARM_SIZE}`,
      { farm_size: farmSize }, 
      { "Content-Type": "application/json" } 
    );

    return response; 
  } catch (error: any) {
    console.error("Error updating user's farm size:", error);
    throw error;
  }
};







/**
 * Service function to create an OTP token for email change.
 * Backend will generate OTP and OTP token.
 */
export const createOtpToken = async (email: String, new_email: String) => {
  try {

    const response = await apiConnector(
      "POST",
      `${API_ROUTES.CREATE_OTP_TOKEN}`, 
      { email, new_email },
      { "Content-Type": "application/json" }
    );

    return response; 
  } catch (error: any) {
    console.error("Error creating OTP token:", error);
    throw error;
  }
};



/**
 * Service function to resend OTP for email change.
 * Backend will find the active OTP token for the user, increment resend_count, and send a new OTP.
 */



export const resendEmailChangeOtp = async () => {
  try {
    const response = await apiConnector(
      "POST",
      `${API_ROUTES.RESEND_OTP}`
    );

    return response;
  } catch (error: any) {
    console.error("Error resending OTP:", error);

    if (error.response?.status === 429) {
      throw new Error("Resend limit reached. Please restart the email change process.");
    } else if (error.response?.status === 404) {
      throw new Error("OTP token not found or expired. Please restart the email change process.");
    }

    throw error;
  }
};


export interface DeleteAccountRequest {
  password: string;
}

export const deleteUser = async ({ password }: DeleteAccountRequest) => {
  try {
    const bodyData = { password };
    const response = await apiConnector(
      "DELETE",
      `${API_ROUTES.DELETE_USER}`,
      bodyData,
      { "Content-Type": "application/json" }
    );

    return response;
  } catch (error: any) {
    console.error("Error deleting user:", error);
    throw error;
  }
};