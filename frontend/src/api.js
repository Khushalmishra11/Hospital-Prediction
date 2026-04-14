import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to add auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("firebaseToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (email, password, fullName) =>
    apiClient.post("/auth/register", {
      email,
      password,
      full_name: fullName,
    }),
  verifyToken: () => apiClient.post("/auth/verify-token"),
  getProfile: () => apiClient.get("/auth/profile"),
};

export const predictionAPI = {
  predict: (data) => apiClient.post("/predict", data),
  getHistory: (limit = 50) => apiClient.get("/predictions/history", { params: { limit } }),
  getStatistics: () => apiClient.get("/predictions/statistics"),
  deletePrediction: (predictionId) => apiClient.delete(`/predictions/${predictionId}`),
};

export const trainingAPI = {
  trainModel: () => apiClient.post("/train"),
};

export default apiClient;
