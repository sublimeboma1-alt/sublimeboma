import { apiClient } from './apiClient'

const JETON_ENDPOINT = '/frais_scolaires/api/jetons/valider/'

export async function validerCodeJeton(code) {
  const data = await apiClient.post(JETON_ENDPOINT, { code })
  return data
}