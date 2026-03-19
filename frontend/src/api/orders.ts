import api from './http'

type OrdersPageParams = {
  page?: number
  size?: number
  patient_id?: number
  owner_id?: number
  archived?: boolean
  resulted?: boolean
  created_date?: string
}

export async function getOrdersPage(params: OrdersPageParams) {
  const res = await api.get('/orders', { params })
  return res.data
}

export async function getOrder(orderId: number | string) {
  const res = await api.get(`/orders/${orderId}`)
  return res.data
}

export async function updateOrder(orderId: number, data: any) {
  const res = await api.patch(`/orders/${orderId}`, data)
  return res.data
}

export async function toggleOrderArchive(orderId: number) {
  const res = await api.patch(`/orders/${orderId}/archive`)
  return res.data
}

export async function getPatientOrders(patientId: number) {
  const res = await api.get(`/patients/${patientId}/orders`)
  return res.data
}

export async function createOrder(data: any) {
  const res = await api.post('/orders/', data)
  return res.data
}

export async function collectSpecimen(specimenId: string) {
  const res = await api.patch(`/orders/barcode/${specimenId}/collect`)
  return res.data
}

export async function receiveSpecimen(specimenId: string) {
  const res = await api.patch(`/orders/barcode/${specimenId}/receive`)
  return res.data
}

export async function printSpecimen(specimenId: string) {
  const res = await api.patch(`/orders/barcode/${specimenId}/print`)
  return res.data
}
