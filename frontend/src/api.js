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

export const doctorOpsAPI = {
  createOrUpdateDoctor: (payload) => apiClient.post("/doctors", payload),
  updateDoctorStatus: (doctorId, status) =>
    apiClient.patch(`/doctors/${doctorId}/status`, { status }),
  getAvailability: (specialty) =>
    apiClient.get("/doctors/availability", { params: { specialty } }),
  getAvailableForSlot: (slotStart, slotEnd, specialty) =>
    apiClient.get("/doctors/available-slot", {
      params: {
        slot_start: slotStart,
        slot_end: slotEnd,
        specialty,
      },
    }),
};

export const schedulingAPI = {
  upsertShift: (payload) => apiClient.post("/shifts", payload),
  getSlots: (date, specialty) => apiClient.get("/slots", { params: { date, specialty } }),
  getAppointments: (params) => apiClient.get("/appointments", { params }),
  createAppointment: (payload) => apiClient.post("/appointments", payload),
  updateAppointmentStatus: (appointmentId, status) =>
    apiClient.patch(`/appointments/${appointmentId}/status`, { status }),
};

export const queueAPI = {
  logEvent: (payload) => apiClient.post("/queue/events", payload),
  getLiveSummary: () => apiClient.get("/queue/live"),
};

export const optimizerAPI = {
  recommendDoctor: (specialty) =>
    apiClient.get("/optimizer/recommend-doctor", { params: { specialty } }),
};

export default apiClient;
