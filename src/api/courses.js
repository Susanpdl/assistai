// Course & enrollment API calls, mapped to the backend's Phase 2 endpoints.
import { apiFetch } from './client.js'

async function json(res) {
  if (!res.ok) {
    const err = new Error('Request failed')
    err.status = res.status
    throw err
  }
  return res.json()
}

export const listCourses = () => apiFetch('/courses').then(json)

export const createCourse = (code, name) =>
  apiFetch('/courses', { method: 'POST', body: JSON.stringify({ code, name }) }).then(json)

export const enroll = (joinCode) =>
  apiFetch('/courses/enroll', { method: 'POST', body: JSON.stringify({ join_code: joinCode }) }).then(
    json,
  )

export const listEnrollments = (courseId, status) =>
  apiFetch(`/courses/${courseId}/enrollments${status ? `?status_filter=${status}` : ''}`).then(json)

export const decide = (enrollmentId, decision) =>
  apiFetch(`/enrollments/${enrollmentId}/decision`, {
    method: 'POST',
    body: JSON.stringify({ decision }),
  }).then(json)
