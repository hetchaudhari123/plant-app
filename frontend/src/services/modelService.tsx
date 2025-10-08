import { apiConnector, modelServiceInstance } from "./apiconnector";
import { API_ROUTES } from "../config/apiRoutes";

export const getAllModels = async (
  status?: string,
  modelType?: string
) => {
  try {
    const params: Record<string, string> = {};
    if (status) params.status = status;
    if (modelType) params.model_type = modelType;
    
    const response = await apiConnector(
      "GET",
      API_ROUTES.GET_ALL_MODELS,  
      null,  
      { "Content-Type": "application/json" },
      params,  
      modelServiceInstance  
    );

    return response;
  } catch (error: unknown) {
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
      `${API_ROUTES.CREATE_PREDICTION}/${modelName}`, 
      formData,
      {}, 
      {}
    );

    return response;
  } catch (error: unknown) {
    console.error("Error creating prediction:", error);
    throw error;
  }
};

export interface PaginationRequest {
  skip?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: number;
}

export interface Prediction {
  prediction_id: string;
  disease: string;
  crop: string;
  confidence: number;
  date: string;
  model_name: string;
  image_url: string;
}

export interface PredictionResponse {
  predictions: Prediction[];
  total: number;
  skip: number;
  limit: number;
}

export const getUserPredictions = async (
  pagination?: PaginationRequest
): Promise<PredictionResponse> => {
  try {
    // Default pagination values
    const requestBody: PaginationRequest = {
      skip: pagination?.skip ?? 0,
      limit: pagination?.limit ?? 5,
      sort_by: pagination?.sort_by ?? "created_at",
      sort_order: pagination?.sort_order ?? -1,
    };

    const response = await apiConnector(
      "POST",
      API_ROUTES.GET_USER_PREDICTIONS,
      requestBody,
      {
        "Content-Type": "application/json",
      },
      {}
    );

    // Extract only the required fields from each prediction
    const filteredPredictions = response.predictions.map((pred: any) => ({
      prediction_id: pred.prediction_id,
      disease: pred.disease,
      crop: pred.crop,
      confidence: pred.raw_output?.primary_confidence ?? 0,
      date: pred.created_at,
      model_name: pred.model_name,
      image_url: pred.image_url,
    }));


    return {
      predictions: filteredPredictions,
      total: response.total,
      skip: response.skip,
      limit: response.limit,
    };
  } catch (error: unknown) {
    console.error("Error fetching user predictions:", error);
    throw error;
  }
};





interface DeletePredictionRequest {
  prediction_id: string;
}

interface DeletePredictionResponse {
  success: boolean;
  message: string;
  prediction_id: string;
}

export const deletePrediction = async (
  predictionId: string
): Promise<DeletePredictionResponse> => {
  try {
    const requestBody: DeletePredictionRequest = {
      prediction_id: predictionId,
    };

    const response = await apiConnector(
      "POST",
      API_ROUTES.DELETE_PREDICTION,
      requestBody,
      {
        "Content-Type": "application/json",
      },
      {}
    );

    return {
      success: response.success,
      message: response.message,
      prediction_id: response.prediction_id,
    };
  } catch (error: unknown) {
    console.error("Error deleting prediction:", error);
    throw error;
  }
};