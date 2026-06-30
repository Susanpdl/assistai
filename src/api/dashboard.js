// Instructor dashboard API — Phase 8.
import { apiFetch } from './client.js'

async function json(res) {
  if (!res.ok) {
    const err = new Error('Request failed')
    err.status = res.status
    throw err
  }
  return res.json()
}

async function ok(res) {
  if (!res.ok && res.status !== 204) {
    const err = new Error('Request failed')
    err.status = res.status
    throw err
  }
}

export const getDashboard = (courseId) =>
  apiFetch(`/courses/${courseId}/dashboard`).then(json)

export const listEscalations = (courseId) =>
  apiFetch(`/courses/${courseId}/escalations`).then(json)

export const answerEscalation = (escalationId, answer) =>
  apiFetch(`/escalations/${escalationId}/answer`, {
    method: 'POST',
    body: JSON.stringify({ answer }),
  }).then(ok)
