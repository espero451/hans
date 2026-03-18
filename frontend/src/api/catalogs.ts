import api from './http'

export async function getTests() {
  const res = await api.get('/tests/')
  return res.data
}

export async function getServices() {
  const res = await api.get('/services/')
  return res.data
}

export async function getSpecimenType(specimenTypeId: number) {
  const res = await api.get(`/specimens/${specimenTypeId}`)
  return res.data
}

export async function getTubes() {
  const res = await api.get('/tubes/')
  return res.data
}
