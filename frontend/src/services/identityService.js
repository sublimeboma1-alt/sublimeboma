import { API_ENDPOINTS, apiClient } from './apiClient'

export const defaultIdentity = {
  nom: 'Complexe Scolaire Sublime',
  espace: 'Administration',
  sigle: 'CS',
}

export async function fetchIdentity() {
  try {
    return await apiClient.get(API_ENDPOINTS.noyau.identite)
  } catch {
    return defaultIdentity
  }
}
