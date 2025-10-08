import axios from "axios";
import { MODEL_SERVICE_URL, APP_SERVICE_URL } from "../config/api";
import { logout } from "./authService";
import { setUser } from "../redux/slices/authSlice";
import store from "../redux/store";



// Shared response interceptor for 401 handling
const responseInterceptor = async (error: unknown) => {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) {
      try {
        await logout();
        store.dispatch(setUser(null));
      } catch (logoutError) {
        console.error("Error during automatic logout:", logoutError);
      }
    }
  } else {
    console.error("Unknown error type caught in interceptor:", error);
  }

  return Promise.reject(error);
};

// App Service instance (localhost:8000)
const appServiceInstance = axios.create({
  baseURL: APP_SERVICE_URL,
  withCredentials: true,
});
appServiceInstance.interceptors.response.use(
  (response) => response,
  responseInterceptor
);

// Model Service instance (localhost:8002)
const modelServiceInstance = axios.create({
  baseURL: MODEL_SERVICE_URL,
  withCredentials: true,
});
modelServiceInstance.interceptors.response.use(
  (response) => response,
  responseInterceptor
);

// Generic API connector with service selection
export const apiConnector = async (
  method: "GET" | "POST" | "PUT" | "DELETE",
  url: string,
  bodyData: any = null,
  headers: Record<string, string> = {},
  params: Record<string, any> = {},
  instance = appServiceInstance  // Default to app service
) => {
  const res = await instance({ method, url, data: bodyData, headers, params });
  return res.data;
};

// Export instances for direct use
export { appServiceInstance, modelServiceInstance };