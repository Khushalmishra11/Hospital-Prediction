import React, { useEffect, useState } from "react";
import { queueAPI } from "../api";

export function QueueDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchSummary = async () => {
    try {
      const response = await queueAPI.getLiveSummary();
      setSummary(response.data);
      setLastUpdated(new Date());
      setError("");
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to fetch queue summary");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
    const id = setInterval(fetchSummary, 15000);
    return () => clearInterval(id);
  }, []);

  if (loading) {
    return <div className="text-gray-600">Loading live queue data...</div>;
  }

  if (error) {
    return <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700">{error}</div>;
  }

  const byDoctor = summary?.by_doctor || {};

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">Live Queue Dashboard</h2>
        <button className="btn-secondary" onClick={fetchSummary} type="button">Refresh</button>
      </div>

      <p className="text-sm text-gray-500">
        Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : "-"} (auto-refresh every 15s)
      </p>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <StatCard title="Waiting" value={summary?.total_waiting ?? 0} color="text-blue-600" />
        <StatCard title="In Consult" value={summary?.in_consult ?? 0} color="text-indigo-600" />
        <StatCard title="Completed Today" value={summary?.completed_today ?? 0} color="text-green-600" />
        <StatCard title="No-show Today" value={summary?.no_show_today ?? 0} color="text-red-600" />
        <StatCard title="Avg Wait (min)" value={summary?.avg_wait_minutes_checked_in ?? 0} color="text-orange-600" />
      </div>

      <div className="bg-white border rounded-lg p-4">
        <h3 className="font-semibold mb-3">Queue by Doctor</h3>
        {Object.keys(byDoctor).length === 0 ? (
          <p className="text-sm text-gray-600">No queue activity found for today.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-2">Doctor ID</th>
                  <th className="text-left p-2">Waiting Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(byDoctor).map(([doctorId, waiting]) => (
                  <tr key={doctorId} className="border-t">
                    <td className="p-2">{doctorId}</td>
                    <td className="p-2">{waiting}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, color }) {
  return (
    <div className="bg-white border rounded-lg p-4">
      <p className="text-xs text-gray-500">{title}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

export default QueueDashboard;
