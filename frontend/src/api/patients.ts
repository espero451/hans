import api from './http'

type PatientsPageParams = {
  skip?: number
  limit?: number
  q?: string
  species_id?: number
  owner_id?: number
}

type PatientOption = {
  label: string
  value: number
}

export async function getPatientsPage(params: PatientsPageParams) {
  const res = await api.get('/patients/', { params })
  return res.data
}

export async function searchPatientsByName(query: string, limit = 20): Promise<PatientOption[]> {
  const trimmed = query.trim()
  if (trimmed.length < 2) return []
  const data = await getPatientsPage({ q: trimmed, limit })
  return (data.items || []).map((patient: any) => ({
    label: patient.name,
    value: patient.id,
  }))
}

export async function getPatient(patientId: number | string) {
  const res = await api.get(`/patients/${patientId}`)
  return res.data
}

export async function createPatient(data: any) {
  const res = await api.post('/patients/', data)
  return res.data
}

export async function patchPatient(patientId: number, data: any) {
  const res = await api.patch(`/patients/${patientId}`, data)
  return res.data
}

export async function getSpecies() {
  const res = await api.get('/species/')
  return res.data
}

export async function getPatientPhoto(patientId: number, responseType: 'blob' = 'blob') {
  const res = await api.get(`/patients/${patientId}/photo`, { responseType })
  return res.data
}

export async function uploadPatientPhoto(patientId: number, form: FormData) {
  const res = await api.post(`/patients/${patientId}/photo`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}
