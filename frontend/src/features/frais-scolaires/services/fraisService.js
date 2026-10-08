import { API_ENDPOINTS, apiClient } from '../../../services/apiClient'

function results(payload) {
  return payload?.results || []
}

function queryString(params = {}) {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null)).toString()
  return query ? `?${query}` : ''
}

export async function fetchFeesDashboard(params = {}) {
  return apiClient.get(`${API_ENDPOINTS.frais.dashboard}${queryString(params)}`)
}
export async function fetchFeesStatistics(params = {}) {
  return apiClient.get(`${API_ENDPOINTS.frais.statistics}${queryString(params)}`)
}

export async function fetchDossiers(params = {}) {
  return results(await apiClient.get(`${API_ENDPOINTS.frais.dossiers}${queryString(params)}`))
}

export async function fetchPayments(params = {}) {
  return results(await apiClient.get(`${API_ENDPOINTS.frais.paiements}${queryString(params)}`))
}

export async function createPayment(payload) {
  return apiClient.post(API_ENDPOINTS.frais.paiements, payload)
}

export async function fetchFeesReferences() { return apiClient.get(API_ENDPOINTS.frais.references) }
export async function fetchYears() { return results(await apiClient.get(API_ENDPOINTS.frais.annees)) }
export async function createYear(payload) { return apiClient.post(API_ENDPOINTS.frais.annees, payload) }
export async function fetchTariffs(params = {}) { return results(await apiClient.get(`${API_ENDPOINTS.frais.tarifs}${queryString(params)}`)) }
export async function createTariff(payload) { return apiClient.post(API_ENDPOINTS.frais.tarifs, payload) }
export async function applyTariff(tarifId) { return apiClient.post(API_ENDPOINTS.frais.apply, { tarif_id: tarifId }) }
export async function fetchEleveDetail(eleveId, params = {}) { return apiClient.get(`${API_ENDPOINTS.frais.eleveDetail(eleveId)}${queryString(params)}`) }

export async function exportSchoolData(params = {}) {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null)).toString()
  const blob = await apiClient.getBlob(`${API_ENDPOINTS.frais.exports}?${query}`)
  const extension = params.format === 'pdf' ? 'pdf' : 'xlsx'
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${params.scope === 'frais' ? 'rapport_frais' : 'inscriptions'}.${extension}`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(link.href)
}
