import api from "./http"

export async function getTests() {
  const res = await api.get("/tests/")
  return res.data
}

export async function createTest(data: any) {
  const res = await api.post("/tests/", data)
  return res.data
}

export async function updateTest(id: number, data: any) {
  const res = await api.put(`/tests/${id}`, data)
  return res.data
}

export async function deleteTest(id: number) {
  await api.delete(`/tests/${id}`)
}

// use:
// import { getTests, createTest } from "../api/tests"

// async function loadTests() {
//   tests.value = await getTests()
// }
