import { apiClient } from './apiClient'

const JETON_ENDPOINT = '/frais_scolaires/api/jetons/valider/'
const QUITTER_JETON_ENDPOINT = '/frais_scolaires/api/jetons/quitter/'

export async function validerCodeJeton(code) {
  const data = await apiClient.post(JETON_ENDPOINT, { code })
  return data
}

export function quitterModeFinance() {
  return apiClient.post(QUITTER_JETON_ENDPOINT, {})
}
