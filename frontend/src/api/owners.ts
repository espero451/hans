import api from './http'

export async function getOwners() {
  const res = await api.get('/owners/')
  return res.data
}

export async function createOwner(data: any) {
  const res = await api.post('/owners/', data)
  return res.data
}

export async function deleteOwner(id: number) {
  await api.delete(`/owners/${id}`)
}

export async function updateOwner(id: number, data: any) {
  const res = await api.put(`/owners/${id}`, data)
  return res.data
}
