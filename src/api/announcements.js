// Announcements API — Phase 7.
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

export const list = (courseId) =>
  apiFetch(`/courses/${courseId}/announcements`).then(json)

export const post = (courseId, text) =>
  apiFetch(`/courses/${courseId}/announcements`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  }).then(json)

export const remove = (announcementId) =>
  apiFetch(`/announcements/${announcementId}`, { method: 'DELETE' }).then(ok)

export const comment = (announcementId, text) =>
  apiFetch(`/announcements/${announcementId}/comments`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  }).then(json)

export const deleteComment = (commentId) =>
  apiFetch(`/comments/${commentId}`, { method: 'DELETE' }).then(ok)
