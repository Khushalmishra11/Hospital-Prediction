import React, { useEffect, useMemo, useState } from "react";
import { queueAPI, schedulingAPI } from "../api";

const ACTIONS = [
  { label: "Check In", status: "checked_in", eventType: "check_in" },
  { label: "Start", status: "in_consult", eventType: "consult_start" },
  { label: "Complete", status: "completed", eventType: "consult_end" },
  { label: "No Show", status: "no_show", eventType: "no_show" },
];

const STATUS_BADGE = {
  booked: "bg-blue-100 text-blue-800",
  checked_in: "bg-yellow-100 text-yellow-800",
  in_consult: "bg-indigo-100 text-indigo-800",
  completed: "bg-green-100 text-green-800",
  no_show: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
};

export function AppointmentsList() {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const [filters, setFilters] = useState({ date: today, doctor_id: "", status: "" });
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const parseError = (err) => err?.response?.data?.detail || "Request failed";

  const fetchAppointments = async () => {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const params = {
        date: filters.date || undefined,
        doctor_id: filters.doctor_id || undefined,
        status: filters.status || undefined,
        limit: 200,
      };
      const response = await schedulingAPI.getAppointments(params);
      setAppointments(response.data.appointments || []);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, []);

  const runAction = async (row, action) => {
    setActionLoadingId(`${row.id}:${action.status}`);
    setMessage("");
    setError("");
    try {
      await schedulingAPI.updateAppointmentStatus(row.id, action.status);
      await queueAPI.logEvent({
        appointment_id: row.id,
        doctor_id: row.doctor_id,
        event_type: action.eventType,
        source: "appointments_list",
      });
      setMessage(`${action.label} applied for appointment ${row.id}.`);
      await fetchAppointments();
    } catch (err) {
      setError(parseError(err));
    } finally {
      setActionLoadingId("");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">Appointments List</h2>
        <button className="btn-secondary" type="button" onClick={fetchAppointments}>Refresh</button>
      </div>

      {message && <div className="p-3 bg-green-50 border border-green-200 rounded text-green-700">{message}</div>}
      {error && <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700">{error}</div>}

      <div className="bg-gray-50 border rounded-lg p-4 grid grid-cols-1 md:grid-cols-4 gap-3">
        <input
          className="input-field"
          type="date"
          value={filters.date}
          onChange={(e) => setFilters({ ...filters, date: e.target.value })}
        />
        <input
          className="input-field"
          placeholder="Doctor ID (optional)"
          value={filters.doctor_id}
          onChange={(e) => setFilters({ ...filters, doctor_id: e.target.value })}
        />
        <select
          className="input-field"
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
        >
          <option value="">All status</option>
          <option value="booked">booked</option>
          <option value="checked_in">checked_in</option>
          <option value="in_consult">in_consult</option>
          <option value="completed">completed</option>
          <option value="no_show">no_show</option>
          <option value="cancelled">cancelled</option>
        </select>
        <button className="btn-primary" type="button" onClick={fetchAppointments}>
          Apply Filters
        </button>
      </div>

      {loading ? (
        <div className="text-gray-600">Loading appointments...</div>
      ) : appointments.length === 0 ? (
        <div className="text-gray-600">No appointments found for selected filters.</div>
      ) : (
        <div className="overflow-x-auto border rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-2">ID</th>
                <th className="text-left p-2">Patient</th>
                <th className="text-left p-2">Doctor</th>
                <th className="text-left p-2">Slot</th>
                <th className="text-left p-2">Status</th>
                <th className="text-left p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((row) => (
                <tr key={row.id} className="border-t align-top">
                  <td className="p-2 font-mono text-xs">{row.id}</td>
                  <td className="p-2">{row.patient_id}</td>
                  <td className="p-2">{row.doctor_id}</td>
                  <td className="p-2 whitespace-nowrap">
                    {row.slot_start ? new Date(row.slot_start).toLocaleString() : "-"}
                  </td>
                  <td className="p-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${STATUS_BADGE[row.status] || "bg-gray-100 text-gray-700"}`}>
                      {row.status}
                    </span>
                  </td>
                  <td className="p-2">
                    <div className="flex flex-wrap gap-2">
                      {ACTIONS.map((action) => (
                        <button
                          key={`${row.id}_${action.status}`}
                          type="button"
                          className="px-2 py-1 rounded border text-xs hover:bg-blue-50"
                          onClick={() => runAction(row, action)}
                          disabled={actionLoadingId === `${row.id}:${action.status}`}
                        >
                          {actionLoadingId === `${row.id}:${action.status}` ? "..." : action.label}
                        </button>
                      ))}
                    </div>
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

export default AppointmentsList;
