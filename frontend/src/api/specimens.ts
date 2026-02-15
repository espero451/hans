import api from "./http"

export async function getSpecimens() {
  const res = await api.get("/specimens/")
  return res.data
}

export async function createSpecimen(data: any) {
  const res = await api.post("/specimens/", data)
  return res.data
}

export async function updateSpecimen(id: number, data: any) {
  const res = await api.put(`/specimens/${id}`, data)
  return res.data
}

export async function deleteSpecimen(id: number) {
  await api.delete(`/specimens/${id}`)
}
