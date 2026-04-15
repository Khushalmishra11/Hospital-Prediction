import React, { useState } from "react";
import { queueAPI, schedulingAPI } from "../api";

const STATUS_EVENT_MAP = {
  checked_in: "check_in",
  in_consult: "consult_start",
  completed: "consult_end",
  no_show: "no_show",
  cancelled: "cancel",
};

export function AppointmentActions() {
  const [appointmentId, setAppointmentId] = useState("");
  const [doctorId, setDoctorId] = useState("");
  const [status, setStatus] = useState("checked_in");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const parseError = (err) => err?.response?.data?.detail || "Request failed";

  const runAction = async () => {
    setLoading(true);
    setMessage("");
    setError("");

    try {
      await schedulingAPI.updateAppointmentStatus(appointmentId, status);

      const eventType = STATUS_EVENT_MAP[status];
      if (eventType && doctorId) {
        await queueAPI.logEvent({
          appointment_id: appointmentId,
          doctor_id: doctorId,
          event_type: eventType,
          source: "ops_ui",
        });
      }

      setMessage(`Appointment updated to '${status}' successfully.`);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-800">Appointment Status Actions</h2>
      <p className="text-sm text-gray-600">
        Use this panel to quickly move appointments through queue lifecycle. If you provide Doctor ID, a queue event is logged too.
      </p>

      {message && <div className="p-3 bg-green-50 border border-green-200 rounded text-green-700">{message}</div>}
      {error && <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700">{error}</div>}

      <div className="bg-gray-50 border rounded-lg p-4 space-y-3 max-w-xl">
        <input
          className="input-field"
          placeholder="Appointment ID"
          value={appointmentId}
          onChange={(e) => setAppointmentId(e.target.value)}
        />
        <input
          className="input-field"
          placeholder="Doctor ID (optional but recommended for queue event)"
          value={doctorId}
          onChange={(e) => setDoctorId(e.target.value)}
        />
        <select
          className="input-field"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="checked_in">checked_in</option>
          <option value="in_consult">in_consult</option>
          <option value="completed">completed</option>
          <option value="no_show">no_show</option>
          <option value="cancelled">cancelled</option>
        </select>

        <button
          type="button"
          className="btn-primary"
          onClick={runAction}
          disabled={loading || !appointmentId}
        >
          {loading ? "Updating..." : "Apply Action"}
        </button>
      </div>
    </div>
  );
}

export default AppointmentActions;
