// Course content (documents) API — Phase 3 ingestion endpoints.
import { API_BASE, apiFetch } from './client.js'

async function json(res) {
  if (!res.ok) {
    const err = new Error('Request failed')
    err.status = res.status
    throw err
  }
  return res.json()
}

export const listDocuments = (courseId) =>
  apiFetch(`/courses/${courseId}/documents`).then(json)

// Multipart upload — note we do NOT set Content-Type, so the browser adds the
// multipart boundary itself. `credentials: 'include'` carries the session cookie.
export const uploadDocument = (courseId, file) => {
  const form = new FormData()
  form.append('file', file)
  return fetch(`${API_BASE}/courses/${courseId}/documents`, {
    method: 'POST',
    credentials: 'include',
    body: form,
  }).then(json)
}

export const reindexDocument = (documentId) =>
  apiFetch(`/documents/${documentId}/reindex`, { method: 'POST' }).then(json)

export const deleteDocument = (documentId) =>
  fetch(`${API_BASE}/documents/${documentId}`, {
    method: 'DELETE',
    credentials: 'include',
  }).then((res) => {
    if (!res.ok && res.status !== 204) {
      const err = new Error('Request failed')
      err.status = res.status
      throw err
    }
  })
