import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { predictionAPI } from "../api";
import PredictionForm from "../components/PredictionForm";
import PredictionHistory from "../components/PredictionHistory";
import { LogOut, TrendingUp, AlertTriangle, Clock } from "lucide-react";

export function DashboardPage() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState("predict");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!currentUser) {
      navigate("/login");
    }
  }, [currentUser, navigate]);

  useEffect(() => {
    fetchStats();
  }, [refreshKey]);

  const fetchStats = async () => {
    try {
      const response = await predictionAPI.getStatistics();
      setStats(response.data.statistics);
    } catch (err) {
      console.error("Failed to fetch statistics:", err);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  const handlePredictionComplete = () => {
    setRefreshKey(refreshKey + 1);
    setActiveTab("history");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-blue-600">Hospital Prediction</h1>
            <p className="text-sm text-gray-600">Welcome, {currentUser?.displayName || currentUser?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-auto inline-flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Total Predictions</p>
                <p className="text-3xl font-bold text-blue-600">{stats?.total_predictions || 0}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-600 opacity-30" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Avg Wait Time</p>
                <p className="text-3xl font-bold text-green-600">{Math.round(stats?.avg_wait_time || 0)} min</p>
              </div>
              <Clock className="w-8 h-8 text-green-600 opacity-30" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">High Risk Cases</p>
                <p className="text-3xl font-bold text-red-600">{stats?.high_risk_count || 0}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-600 opacity-30" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="border-b flex">
            <button
              onClick={() => setActiveTab("predict")}
              className={`px-6 py-4 font-semibold ${
                activeTab === "predict"
                  ? "text-blue-600 border-b-2 border-blue-600"
                  : "text-gray-600 hover:text-gray-800"
              }`}
            >
              Make Prediction
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={`px-6 py-4 font-semibold ${
                activeTab === "history"
                  ? "text-blue-600 border-b-2 border-blue-600"
                  : "text-gray-600 hover:text-gray-800"
              }`}
            >
              History
            </button>
          </div>

          <div className="p-6">
            {activeTab === "predict" ? (
              <PredictionForm onPredictionComplete={handlePredictionComplete} />
            ) : (
              <PredictionHistory key={refreshKey} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
