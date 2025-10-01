import { apiConnector, modelServiceInstance } from "./apiconnector";
import { API_ROUTES } from "../config/apiRoutes";

export const getAllModels = async (
  status?: string,
  modelType?: string
) => {
  try {
    // Build params object (not URLSearchParams)
    const params: Record<string, string> = {};
    if (status) params.status = status;
    if (modelType) params.model_type = modelType;
    
    const response = await apiConnector(
      "GET",
      API_ROUTES.GET_ALL_MODELS,  // Just the path, no query string
      null,  // Changed from {} to null for GET request
      { "Content-Type": "application/json" },
      params,  // Pass params here - axios will build the query string
      modelServiceInstance  
    );

    return response;
  } catch (error: any) {
    console.error("Error fetching models:", error);
    throw error;
  }
};


export const createPrediction = async (
  modelName: string,
  file: File
) => {
  try {
    // Create FormData to send the file
    const formData = new FormData();
    formData.append("file", file);

    // Call the endpoint with model_name in the URL path
    const response = await apiConnector(
      "POST",
      `${API_ROUTES.CREATE_PREDICTION}/${modelName}`, // modelName in URL path
      formData,
      {}, // Don't set Content-Type - browser sets it automatically with multipart boundary
      {}
    );

    return response;
  } catch (error: any) {
    console.error("Error creating prediction:", error);
    throw error;
  }
};