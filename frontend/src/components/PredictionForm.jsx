import React, { useState } from "react";
import { predictionAPI } from "../api";
import { AlertCircle, CheckCircle, Clock, AlertTriangle } from "lucide-react";

export function PredictionForm({ onPredictionComplete }) {
  const [formData, setFormData] = useState({
    day_of_week: 1,
    hour: 10,
    doctor_count: 3,
    scheduled_appointments: 20,
    walk_in_patients: 10,
    avg_consultation_minutes: 15,
    is_holiday: false,
    rain_intensity: 0.2,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === "checkbox" ? checked : type === "number" ? parseFloat(value) : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await predictionAPI.predict(formData);
      setResult(response.data);
      if (onPredictionComplete) {
        onPredictionComplete();
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to make prediction");
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (risk) => {
    if (risk === "HIGH") return "text-red-600";
    if (risk === "MEDIUM") return "text-yellow-600";
    return "text-green-600";
  };

  const getRiskBgColor = (risk) => {
    if (risk === "HIGH") return "bg-red-50 border-red-200";
    if (risk === "MEDIUM") return "bg-yellow-50 border-yellow-200";
    return "bg-green-50 border-green-200";
  };

  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Appointment Prediction</h2>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 mb-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Day of Week</label>
            <select
              name="day_of_week"
              value={formData.day_of_week}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {days.map((day, idx) => (
                <option key={idx} value={idx}>
                  {day}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Hour (0-23)</label>
            <input
              type="number"
              name="hour"
              value={formData.hour}
              onChange={handleChange}
              min="0"
              max="23"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Number of Doctors</label>
            <input
              type="number"
              name="doctor_count"
              value={formData.doctor_count}
              onChange={handleChange}
              min="1"
              max="50"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Scheduled Appointments</label>
            <input
              type="number"
              name="scheduled_appointments"
              value={formData.scheduled_appointments}
              onChange={handleChange}
              min="0"
              max="500"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Walk-in Patients</label>
            <input
              type="number"
              name="walk_in_patients"
              value={formData.walk_in_patients}
              onChange={handleChange}
              min="0"
              max="500"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Avg Consultation (min)</label>
            <input
              type="number"
              name="avg_consultation_minutes"
              value={formData.avg_consultation_minutes}
              onChange={handleChange}
              min="1"
              max="120"
              step="0.5"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rain Intensity (0-1)</label>
            <input
              type="number"
              name="rain_intensity"
              value={formData.rain_intensity}
              onChange={handleChange}
              min="0"
              max="1"
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                name="is_holiday"
                checked={formData.is_holiday}
                onChange={handleChange}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Is Holiday</span>
            </label>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-2 rounded-lg transition duration-200"
        >
          {loading ? "Predicting..." : "Get Prediction"}
        </button>
      </form>

      {result && (
        <div className={`p-6 border rounded-lg ${getRiskBgColor(result.risk_level)}`}>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Prediction Results</h3>

          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg">
              <div className="text-gray-600 text-sm mb-1">Load Score</div>
              <div className="text-2xl font-bold text-blue-600">{result.predicted_load_score}</div>
            </div>

            <div className="bg-white p-4 rounded-lg flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-600" />
              <div>
                <div className="text-gray-600 text-sm">Wait Time</div>
                <div className="text-2xl font-bold text-blue-600">
                  {Math.round(result.expected_wait_minutes)} min
                </div>
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg">
              <div className="text-gray-600 text-sm mb-1">Risk Level</div>
              <div className={`text-2xl font-bold ${getRiskColor(result.risk_level)}`}>
                {result.risk_level}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PredictionForm;
