import api from './http'

type OwnersPageParams = {
  skip?: number
  limit?: number
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
}

export async function getOwners() {
  const res = await api.get('/owners/', {
    params: { skip: 0, limit: 200 },
  })
  return res.data.items
}

export async function getOwnersPage(params: OwnersPageParams) {
  const res = await api.get('/owners/', { params })
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
