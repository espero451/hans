import axios from "axios"

// Centralized Axios instance
const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
})

// Attach JWT token if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
