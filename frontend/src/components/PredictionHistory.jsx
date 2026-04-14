import React, { useState, useEffect } from "react";
import { predictionAPI } from "../api";
import { Trash2, AlertCircle } from "lucide-react";

export function PredictionHistory() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await predictionAPI.getHistory(50);
      setPredictions(response.data.predictions || []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load prediction history");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (predictionId) => {
    if (!window.confirm("Are you sure you want to delete this prediction?")) return;

    try {
      await predictionAPI.deletePrediction(predictionId);
      setPredictions(predictions.filter((p) => p.id !== predictionId));
    } catch (err) {
      setError("Failed to delete prediction");
    }
  };

  const getRiskColor = (risk) => {
    if (risk === "HIGH") return "bg-red-100 text-red-800";
    if (risk === "MEDIUM") return "bg-yellow-100 text-yellow-800";
    return "bg-green-100 text-green-800";
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  if (loading) {
    return <div className="text-center text-gray-600 py-8">Loading history...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Prediction History</h2>

      {predictions.length === 0 ? (
        <p className="text-gray-600 text-center py-8">No predictions yet. Make your first prediction!</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Date</th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Load Score</th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Wait Time</th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Risk Level</th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Doctors</th>
                <th className="px-4 py-2 text-center text-sm font-semibold text-gray-700">Action</th>
              </tr>
            </thead>
            <tbody>
              {predictions.map((prediction) => (
                <tr key={prediction.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-600">{formatDate(prediction.created_at)}</td>
                  <td className="px-4 py-3 text-sm font-semibold text-blue-600">{prediction.predicted_load_score}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {Math.round(prediction.expected_wait_minutes)} min
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getRiskColor(prediction.risk_level)}`}>
                      {prediction.risk_level}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{prediction.input_data?.doctor_count}</td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => handleDelete(prediction.id)}
                      className="text-red-600 hover:text-red-800 transition"
                      title="Delete prediction"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default PredictionHistory;
