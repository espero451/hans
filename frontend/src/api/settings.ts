import api from './http'

export async function getDispatcherStatus() {
  const res = await api.get('/settings/dispatcher/status')
  return res.data
}

export async function restartDispatcher() {
  const res = await api.post('/settings/dispatcher/restart')
  return res.data
}

export async function getDispatcherTrace() {
  const res = await api.get('/settings/dispatcher/trace', {
    responseType: 'text',
  })
  return res.data
}
