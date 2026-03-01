// import api from "./http"

// export async function login(username: string, password: string) {
//   const form = new FormData()
//   form.append("username", username)
//   form.append("password", password)

//   const response = await api.post("/auth/token", form)
//   localStorage.setItem("token", response.data.access_token)
// }

import api from "./http"

export async function login(username: string, password: string) {
  const form = new FormData()
  form.append("username", username)
  form.append("password", password)

  const response = await api.post("/auth/token", form)

  const token = response.data.access_token
  localStorage.setItem("token", token)

  return token
}

export async function getCurrentUser() {
  const response = await api.get("/auth/me")
  return response.data
}

export function logout() {
  localStorage.removeItem("token")
}