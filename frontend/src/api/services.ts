import api from "./http"

export async function getServices() {
  const res = await api.get("/services")
  return res.data
}

export async function createService(data: any) {
  const res = await api.post("/services", data)
  return res.data
}

export async function updateService(id: number, data: any) {
  const res = await api.put(`/services/${id}`, data)
  return res.data
}

export async function deleteService(id: number) {
  await api.delete(`/services/${id}`)
}
