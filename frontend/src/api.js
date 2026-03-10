import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
})

let _getToken = null
let _setToken = null

export function initTokenFunctions(getter, setter) {
  _getToken = getter
  _setToken = setter
}

api.interceptors.request.use((config) => {
  const token = _getToken ? _getToken() : null
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Shared refresh promise — prevents parallel refresh race condition
let _refreshPromise = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    // Skip refresh for auth endpoints
    if (originalRequest.url?.includes('/auth/')) {
      return Promise.reject(error)
    }
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        // Deduplicate: reuse in-flight refresh promise
        if (!_refreshPromise) {
          _refreshPromise = axios.post(`${API_URL}/api/auth/refresh`, {}, { withCredentials: true })
            .finally(() => { _refreshPromise = null })
        }
        const { data } = await _refreshPromise
        if (_setToken) _setToken(data.access_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return api(originalRequest)
      } catch {
        if (_setToken) _setToken(null)
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  }
)

export default api
