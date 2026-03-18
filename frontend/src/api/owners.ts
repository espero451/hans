import api from './http'

type OwnersPageParams = {
  skip?: number
  limit?: number
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
}

type OwnerOption = {
  label: string
  value: number
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

export async function getOwner(ownerId: number) {
  const res = await api.get(`/owners/${ownerId}`)
  return res.data
}

export async function searchOwnersByQuery(query: string, limit = 20): Promise<OwnerOption[]> {
  const trimmed = query.trim()
  if (trimmed.length < 2) return []
  const [firstPage, lastPage] = await Promise.all([
    getOwnersPage({ first_name: trimmed, limit }),
    getOwnersPage({ last_name: trimmed, limit }),
  ])
  const merged = [...(firstPage.items || []), ...(lastPage.items || [])]
  const unique = new Map<number, OwnerOption>()
  for (const owner of merged) {
    unique.set(owner.id, {
      label: `${owner.first_name} ${owner.last_name}`,
      value: owner.id,
    })
  }
  return Array.from(unique.values()).slice(0, limit)
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
