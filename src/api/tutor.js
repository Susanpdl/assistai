// AI Tutor API — Phase 4 (ask + history).
import { apiFetch } from './client.js'

async function json(res) {
  if (!res.ok) {
    const err = new Error('Request failed')
    err.status = res.status
    throw err
  }
  return res.json()
}

export const ask = (courseId, question) =>
  apiFetch(`/courses/${courseId}/ask`, {
    method: 'POST',
    body: JSON.stringify({ question }),
  }).then(json)

export const listMessages = (courseId) =>
  apiFetch(`/courses/${courseId}/messages`).then(json)
