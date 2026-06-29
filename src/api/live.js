// Live sessions & polls API — Phase 5 (HTTP actions + WebSocket).
import { API_BASE, apiFetch } from './client.js'

async function json(res) {
  if (!res.ok) {
    const err = new Error('Request failed')
    err.status = res.status
    throw err
  }
  return res.json()
}

export const activeSession = (courseId) =>
  apiFetch(`/courses/${courseId}/sessions/active`).then(json)

export const startSession = (courseId) =>
  apiFetch(`/courses/${courseId}/sessions`, { method: 'POST' }).then(json)

export const endSession = (sessionId) =>
  apiFetch(`/sessions/${sessionId}/end`, { method: 'POST' }).then(json)

export const pushPoll = (sessionId, question, options) =>
  apiFetch(`/sessions/${sessionId}/activities`, {
    method: 'POST',
    body: JSON.stringify({ question, options }),
  }).then(json)

export const revealPoll = (activityId) =>
  apiFetch(`/activities/${activityId}/reveal`, { method: 'POST' }).then(json)

export const getResults = (activityId) =>
  apiFetch(`/activities/${activityId}/results`).then(json)

// Open the session WebSocket. The session cookie rides along automatically (same-site).
// `onMessage` receives each parsed server message; returns the WebSocket so callers can close it.
export function openSessionSocket(sessionId, onMessage) {
  const wsBase = API_BASE.replace(/^http/, 'ws')
  const ws = new WebSocket(`${wsBase}/ws/sessions/${sessionId}`)
  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data))
    } catch {
      /* ignore malformed frames */
    }
  }
  return ws
}
