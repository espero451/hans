import axios from "axios"

// Centralized Axios instance
const API_BASE_URL = "http://127.0.0.1:8000"
const ACCESS_TOKEN_KEY = "token"
const REFRESH_TOKEN_KEY = "refresh_token"

const api = axios.create({
  baseURL: API_BASE_URL,
})

const refreshClient = axios.create({
  baseURL: API_BASE_URL,
})

function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refreshToken) {
    clearTokens()
    throw new Error("Missing refresh token")
  }
  try {
    const response = await refreshClient.post("/auth/refresh", { refresh_token: refreshToken })
    const newAccessToken = response.data.access_token
    const newRefreshToken = response.data.refresh_token
    localStorage.setItem(ACCESS_TOKEN_KEY, newAccessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken)
    return newAccessToken
  } catch (err) {
    clearTokens()
    throw err
  }
}

// Attach JWT token if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as any
    if (!originalRequest || originalRequest._retry) {
      return Promise.reject(error)
    }
    if (error.response?.status !== 401) {
      return Promise.reject(error)
    }
    const url = originalRequest.url || ""
    if (url.includes("/auth/token") || url.includes("/auth/refresh")) {
      return Promise.reject(error)
    }
    originalRequest._retry = true
    const newAccessToken = await refreshAccessToken()
    originalRequest.headers = originalRequest.headers || {}
    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
    return api(originalRequest)
  },
)

export default api
