// import api from "./http"

// export async function login(username: string, password: string) {
//   const form = new FormData()
//   form.append("username", username)
//   form.append("password", password)

//   const response = await api.post("/auth/token", form)
//   localStorage.setItem("token", response.data.access_token)
// }

import api from "./http"

const ACCESS_TOKEN_KEY = "token"
const REFRESH_TOKEN_KEY = "refresh_token"

function storeTokens(accessToken: string, refreshToken?: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  }
}

export async function login(username: string, password: string) {
  const form = new FormData()
  form.append("username", username)
  form.append("password", password)

  const response = await api.post("/auth/token", form)

  const token = response.data.access_token
  const refreshToken = response.data.refresh_token
  storeTokens(token, refreshToken)

  return token
}

export async function refreshTokens() {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refreshToken) {
    throw new Error("Missing refresh token")
  }
  const response = await api.post("/auth/refresh", { refresh_token: refreshToken })
  const token = response.data.access_token
  const newRefreshToken = response.data.refresh_token
  storeTokens(token, newRefreshToken)
  return token
}

export async function getCurrentUser() {
  const response = await api.get("/auth/me")
  return response.data
}

export function logout() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}
