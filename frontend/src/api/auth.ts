import api from "./http"

export async function login(username: string, password: string) {
  const form = new FormData()
  form.append("username", username)
  form.append("password", password)

  const response = await api.post("/auth/token", form)
  localStorage.setItem("token", response.data.access_token)
}
