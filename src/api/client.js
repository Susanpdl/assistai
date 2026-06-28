// Thin fetch wrapper. `credentials: 'include'` is essential — it sends and receives the
// httpOnly session cookie that the backend sets on login.
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function apiFetch(path, options = {}) {
  return fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
}

export { API_BASE }
