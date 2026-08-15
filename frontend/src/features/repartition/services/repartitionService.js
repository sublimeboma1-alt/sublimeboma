import { API_ENDPOINTS, apiClient } from '../../../services/apiClient'

export function fetchRepartitionDashboard(params = {}) {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value)).toString()
  return apiClient.get(`${API_ENDPOINTS.repartition.dashboard}${query ? `?${query}` : ''}`)
}

export function fetchRepartitionSettings() { return apiClient.get(API_ENDPOINTS.repartition.settings) }
export function saveRepartitionSettings(payload) { return apiClient.post(API_ENDPOINTS.repartition.settings, payload) }
