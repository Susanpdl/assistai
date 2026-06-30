// Attendance API — Phase 6 (rotating code + check-in + roster).
import { apiFetch } from './client.js'

async function json(res) {
  if (!res.ok) {
    const err = new Error('Request failed')
    err.status = res.status
    try {
      err.detail = (await res.json()).detail
    } catch {
      /* ignore */
    }
    throw err
  }
  return res.json()
}

export const getCode = (sessionId) =>
  apiFetch(`/sessions/${sessionId}/attendance/code`).then(json)

export const checkin = (sessionId, code, deviceId) =>
  apiFetch(`/sessions/${sessionId}/attendance/checkin`, {
    method: 'POST',
    body: JSON.stringify({ code, device_id: deviceId }),
  }).then(json)

export const getAttendance = (sessionId) =>
  apiFetch(`/sessions/${sessionId}/attendance`).then(json)

export const getSummary = (courseId) =>
  apiFetch(`/courses/${courseId}/attendance/summary`).then(json)

// A soft per-browser device id (persisted in localStorage). Sturdier in the native app.
export function deviceId() {
  let id = localStorage.getItem('assistai_device_id')
  if (!id) {
    id = (crypto.randomUUID?.() || String(Math.random())).slice(0, 36)
    localStorage.setItem('assistai_device_id', id)
  }
  return id
}
