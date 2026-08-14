import { API_ENDPOINTS, apiClient } from '../../../services/apiClient'

export function fetchSession() {
  return apiClient.get(API_ENDPOINTS.auth.session)
}

export function loginUser(credentials) {
  return apiClient.post(API_ENDPOINTS.auth.login, credentials)
}

export function logoutUser() {
  return apiClient.post(API_ENDPOINTS.auth.logout, {})
}
