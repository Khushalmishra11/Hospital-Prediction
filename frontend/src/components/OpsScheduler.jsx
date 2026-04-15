import React, { useMemo, useState } from "react";
import { doctorOpsAPI, optimizerAPI, schedulingAPI } from "../api";

export function OpsScheduler() {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [doctor, setDoctor] = useState({
    doctor_id: "doc_1",
    name: "Dr. Sharma",
    specialty: "General",
    avg_consultation_minutes: 15,
    shift_start: "09:00",
    shift_end: "17:00",
  });

  const [statusUpdate, setStatusUpdate] = useState({ doctorId: "doc_1", status: "available" });

  const [shift, setShift] = useState({
    doctor_id: "doc_1",
    date: today,
    start_time: "09:00",
    end_time: "13:00",
    slot_duration_minutes: 15,
    is_available: true,
  });

  const [slotQuery, setSlotQuery] = useState({ date: today, specialty: "General" });
  const [slots, setSlots] = useState([]);

  const [appointment, setAppointment] = useState({
    patient_id: "patient_101",
    doctor_id: "doc_1",
    slot_start: "",
    slot_end: "",
    booking_channel: "web",
  });

  const [optimizerSpecialty, setOptimizerSpecialty] = useState("General");
  const [recommendation, setRecommendation] = useState(null);

  const clearNotices = () => {
    setMessage("");
    setError("");
  };

  const parseError = (err) => err?.response?.data?.detail || "Request failed";

  const handleCreateDoctor = async (e) => {
    e.preventDefault();
    clearNotices();
    setLoading(true);
    try {
      await doctorOpsAPI.createOrUpdateDoctor({
        ...doctor,
        avg_consultation_minutes: Number(doctor.avg_consultation_minutes),
      });
      setMessage("Doctor saved successfully.");
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (e) => {
    e.preventDefault();
    clearNotices();
    setLoading(true);
    try {
      await doctorOpsAPI.updateDoctorStatus(statusUpdate.doctorId, statusUpdate.status);
      setMessage("Doctor status updated.");
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleUpsertShift = async (e) => {
    e.preventDefault();
    clearNotices();
    setLoading(true);
    try {
      await schedulingAPI.upsertShift({
        ...shift,
        slot_duration_minutes: Number(shift.slot_duration_minutes),
      });
      setMessage("Shift saved successfully.");
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleGetSlots = async (e) => {
    e.preventDefault();
    clearNotices();
    setLoading(true);
    try {
      const response = await schedulingAPI.getSlots(slotQuery.date, slotQuery.specialty || undefined);
      setSlots(response.data.slots || []);
      setMessage(`Fetched ${response.data.count || 0} slot(s).`);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const chooseSlot = (slot) => {
    setAppointment((prev) => ({
      ...prev,
      doctor_id: slot.doctor_id,
      slot_start: slot.slot_start,
      slot_end: slot.slot_end,
    }));
  };

  const handleCreateAppointment = async (e) => {
    e.preventDefault();
    clearNotices();
    setLoading(true);
    try {
      await schedulingAPI.createAppointment(appointment);
      setMessage("Appointment created successfully.");
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleRecommendDoctor = async () => {
    clearNotices();
    setLoading(true);
    try {
      const response = await optimizerAPI.recommendDoctor(optimizerSpecialty);
      setRecommendation(response.data);
      setMessage("Doctor recommendation ready.");
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Clinic Operations</h2>

      {message && <div className="p-3 bg-green-50 border border-green-200 rounded text-green-700">{message}</div>}
      {error && <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700">{error}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form onSubmit={handleCreateDoctor} className="bg-gray-50 border rounded-lg p-4 space-y-3">
          <h3 className="text-lg font-semibold">1. Create/Update Doctor</h3>
          <input className="input-field" placeholder="Doctor ID" value={doctor.doctor_id} onChange={(e) => setDoctor({ ...doctor, doctor_id: e.target.value })} />
          <input className="input-field" placeholder="Name" value={doctor.name} onChange={(e) => setDoctor({ ...doctor, name: e.target.value })} />
          <input className="input-field" placeholder="Specialty" value={doctor.specialty} onChange={(e) => setDoctor({ ...doctor, specialty: e.target.value })} />
          <input className="input-field" type="number" placeholder="Avg consultation mins" value={doctor.avg_consultation_minutes} onChange={(e) => setDoctor({ ...doctor, avg_consultation_minutes: e.target.value })} />
          <div className="grid grid-cols-2 gap-2">
            <input className="input-field" type="time" value={doctor.shift_start} onChange={(e) => setDoctor({ ...doctor, shift_start: e.target.value })} />
            <input className="input-field" type="time" value={doctor.shift_end} onChange={(e) => setDoctor({ ...doctor, shift_end: e.target.value })} />
          </div>
          <button disabled={loading} className="btn-primary" type="submit">Save Doctor</button>
        </form>

        <form onSubmit={handleUpdateStatus} className="bg-gray-50 border rounded-lg p-4 space-y-3">
          <h3 className="text-lg font-semibold">2. Update Doctor Status</h3>
          <input className="input-field" placeholder="Doctor ID" value={statusUpdate.doctorId} onChange={(e) => setStatusUpdate({ ...statusUpdate, doctorId: e.target.value })} />
          <select className="input-field" value={statusUpdate.status} onChange={(e) => setStatusUpdate({ ...statusUpdate, status: e.target.value })}>
            <option value="available">available</option>
            <option value="busy">busy</option>
            <option value="break">break</option>
            <option value="offline">offline</option>
          </select>
          <button disabled={loading} className="btn-primary" type="submit">Update Status</button>
        </form>

        <form onSubmit={handleUpsertShift} className="bg-gray-50 border rounded-lg p-4 space-y-3">
          <h3 className="text-lg font-semibold">3. Add Shift</h3>
          <input className="input-field" placeholder="Doctor ID" value={shift.doctor_id} onChange={(e) => setShift({ ...shift, doctor_id: e.target.value })} />
          <input className="input-field" type="date" value={shift.date} onChange={(e) => setShift({ ...shift, date: e.target.value })} />
          <div className="grid grid-cols-2 gap-2">
            <input className="input-field" type="time" value={shift.start_time} onChange={(e) => setShift({ ...shift, start_time: e.target.value })} />
            <input className="input-field" type="time" value={shift.end_time} onChange={(e) => setShift({ ...shift, end_time: e.target.value })} />
          </div>
          <input className="input-field" type="number" min="5" max="60" value={shift.slot_duration_minutes} onChange={(e) => setShift({ ...shift, slot_duration_minutes: e.target.value })} />
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={shift.is_available} onChange={(e) => setShift({ ...shift, is_available: e.target.checked })} />
            Shift available
          </label>
          <button disabled={loading} className="btn-primary" type="submit">Save Shift</button>
        </form>

        <form onSubmit={handleGetSlots} className="bg-gray-50 border rounded-lg p-4 space-y-3">
          <h3 className="text-lg font-semibold">4. Fetch Slots</h3>
          <input className="input-field" type="date" value={slotQuery.date} onChange={(e) => setSlotQuery({ ...slotQuery, date: e.target.value })} />
          <input className="input-field" placeholder="Specialty" value={slotQuery.specialty} onChange={(e) => setSlotQuery({ ...slotQuery, specialty: e.target.value })} />
          <button disabled={loading} className="btn-primary" type="submit">Get Slots</button>

          <div className="max-h-48 overflow-y-auto space-y-2">
            {slots.map((slot) => (
              <button
                key={`${slot.doctor_id}_${slot.slot_start}`}
                type="button"
                className="w-full text-left border rounded p-2 hover:bg-blue-50"
                onClick={() => chooseSlot(slot)}
              >
                <div className="font-medium">{slot.doctor_name} ({slot.specialty})</div>
                <div className="text-sm text-gray-600">{new Date(slot.slot_start).toLocaleString()} - {new Date(slot.slot_end).toLocaleTimeString()}</div>
              </button>
            ))}
          </div>
        </form>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form onSubmit={handleCreateAppointment} className="bg-gray-50 border rounded-lg p-4 space-y-3">
          <h3 className="text-lg font-semibold">5. Create Appointment</h3>
          <input className="input-field" placeholder="Patient ID" value={appointment.patient_id} onChange={(e) => setAppointment({ ...appointment, patient_id: e.target.value })} />
          <input className="input-field" placeholder="Doctor ID" value={appointment.doctor_id} onChange={(e) => setAppointment({ ...appointment, doctor_id: e.target.value })} />
          <input className="input-field" type="datetime-local" value={appointment.slot_start ? appointment.slot_start.slice(0, 16) : ""} onChange={(e) => setAppointment({ ...appointment, slot_start: `${e.target.value}:00` })} />
          <input className="input-field" type="datetime-local" value={appointment.slot_end ? appointment.slot_end.slice(0, 16) : ""} onChange={(e) => setAppointment({ ...appointment, slot_end: `${e.target.value}:00` })} />
          <button disabled={loading} className="btn-primary" type="submit">Book Appointment</button>
        </form>

        <div className="bg-gray-50 border rounded-lg p-4 space-y-3">
          <h3 className="text-lg font-semibold">6. Recommend Doctor</h3>
          <input className="input-field" placeholder="Specialty" value={optimizerSpecialty} onChange={(e) => setOptimizerSpecialty(e.target.value)} />
          <button disabled={loading} className="btn-primary" type="button" onClick={handleRecommendDoctor}>Get Recommendation</button>
          {recommendation && (
            <div className="p-3 bg-white border rounded">
              <div><span className="font-semibold">Doctor:</span> {recommendation.name} ({recommendation.doctor_id})</div>
              <div><span className="font-semibold">Specialty:</span> {recommendation.specialty}</div>
              <div><span className="font-semibold">Status:</span> {recommendation.status}</div>
              <div><span className="font-semibold">Load Score:</span> {recommendation.weighted_load_score}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default OpsScheduler;
