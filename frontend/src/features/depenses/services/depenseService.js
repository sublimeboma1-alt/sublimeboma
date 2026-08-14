import { API_ENDPOINTS, apiClient } from '../../../services/apiClient'

export async function fetchCategories() {
  const payload = await apiClient.get(API_ENDPOINTS.depense.categories)
  return payload?.results || []
}