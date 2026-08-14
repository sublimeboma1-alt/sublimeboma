import { API_ENDPOINTS, apiClient } from '../../../services/apiClient'

function results(payload) {
  return payload?.results || []
}

export async function fetchFeesDashboard() {
  return apiClient.get(API_ENDPOINTS.frais.dashboard)
}
export async function fetchFeesStatistics(params = {}) {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value)).toString()
  return apiClient.get(`${API_ENDPOINTS.frais.statistics}${query ? `?${query}` : ''}`)
}

export async function fetchDossiers(params = {}) {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value)).toString()
  return results(await apiClient.get(`${API_ENDPOINTS.frais.dossiers}${query ? `?${query}` : ''}`))
}

export async function fetchPayments() {
  return results(await apiClient.get(API_ENDPOINTS.frais.paiements))
}

export async function createPayment(payload) {
  return apiClient.post(API_ENDPOINTS.frais.paiements, payload)
}

export async function fetchFeesReferences() { return apiClient.get(API_ENDPOINTS.frais.references) }
export async function fetchYears() { return results(await apiClient.get(API_ENDPOINTS.frais.annees)) }
export async function createYear(payload) { return apiClient.post(API_ENDPOINTS.frais.annees, payload) }
export async function fetchTariffs() { return results(await apiClient.get(API_ENDPOINTS.frais.tarifs)) }
export async function createTariff(payload) { return apiClient.post(API_ENDPOINTS.frais.tarifs, payload) }
export async function applyTariff(tarifId) { return apiClient.post(API_ENDPOINTS.frais.apply, { tarif_id: tarifId }) }
export async function fetchEleveDetail(eleveId) { return apiClient.get(API_ENDPOINTS.frais.eleveDetail(eleveId)) }

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
