import api from './http'

export async function updateResult(resultId: number, data: any) {
  const res = await api.patch(`/results/${resultId}`, data)
  return res.data
}

export async function toggleVerifyResult(resultId: number) {
  const res = await api.post(`/results/${resultId}/verify`)
  return res.data
}
