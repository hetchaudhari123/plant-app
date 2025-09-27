import axios from "axios";
import { API_BASE_URL } from "../config/api";

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});



// Response interceptor → handle 401 (expired access token)
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const { default: store } = await import("../redux/store");
      store.dispatch({ type: "auth/logout" });
    }
    return Promise.reject(error);
  }
);




// 3️⃣ API connector function
export const apiConnector = async (
  method: "GET" | "POST" | "PUT" | "DELETE",
  url: string,
  bodyData: any = null,       // <-- allow any object
  headers: Record<string, string> = {},
  params: Record<string, any> = {}
) => {
  try {
    const res = await axiosInstance({
      method,
      url,
      data: bodyData,
      headers,
      params,
    });
    return res.data; // return only the data
  } catch (err) {
    throw err; // pass error to caller
  }
};
