// Auth API calls, mapped 1:1 to the backend's /auth endpoints.
import { apiFetch } from './client.js'

export async function requestLink(email) {
  const res = await apiFetch('/auth/request', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
  if (!res.ok) throw new Error('Could not send sign-in link')
  return res.json()
}

// Returns the current user, or null if not signed in (401).
export async function getMe() {
  const res = await apiFetch('/auth/me')
  if (res.status === 401) return null
  if (!res.ok) throw new Error('Could not load session')
  return res.json()
}

export async function logout() {
  await apiFetch('/auth/logout', { method: 'POST' })
}
