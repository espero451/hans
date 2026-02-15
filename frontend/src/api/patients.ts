import api from "./http"

export async function getPatients() {
  const res = await api.get("/patients/")
  return res.data
}

export async function createPatient(data: any) {
  const res = await api.post("/patients/", data)
  return res.data
}

export async function deletePatient(id: number) {
  await api.delete(`/patients/${id}`)
}
