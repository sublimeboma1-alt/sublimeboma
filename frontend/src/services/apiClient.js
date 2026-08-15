// URL a modifier manuellement si le frontend et le backend sont sur des domaines differents.
// Exemple : 'https://sublimeboma-production.up.railway.app'
const MANUAL_API_BASE_URL = 'https://sublimeboma-production.up.railway.app'

// Priorite : URL manuelle > variable Vite > domaine actuellement ouvert.
// Laisser MANUAL_API_BASE_URL vide est recommande quand React est servi par Django.
const configuredApiBaseUrl = MANUAL_API_BASE_URL || import.meta.env.VITE_API_BASE_URL || window.location.origin
export const API_BASE_URL = configuredApiBaseUrl.replace(/\/+$/, '')

export const API_ENDPOINTS = {
  auth: {
    session: '/comptes/api/session/',
    login: '/comptes/api/login/',
    logout: '/comptes/api/logout/',
  },
  eleves: {
    list: '/eleves/api/eleves/',
    exportXlsx: '/eleves/api/eleves/export/xlsx/',
    detail: (id) => `/eleves/api/eleves/${id}/`,
    classes: '/eleves/api/classes/',
    references: '/eleves/api/references/',
  },
  frais: {
    dashboard: '/frais_scolaires/api/dashboard/',
    statistics: '/frais_scolaires/api/statistiques/',
    dossiers: '/frais_scolaires/api/dossiers/',
    paiements: '/frais_scolaires/api/paiements/',
    references: '/frais_scolaires/api/references/',
    annees: '/frais_scolaires/api/annees/',
    tarifs: '/frais_scolaires/api/tarifs/',
    apply: '/frais_scolaires/api/appliquer-tarif/',
    exports: '/frais_scolaires/api/exports/',
    eleveDetail: (id) => `/frais_scolaires/api/eleves/${id}/detail/`,
  },
  depense: {
    categories: '/depense/api/categories/',
  },
  repartition: {
    dashboard: '/repartition/api/dashboard/',
    settings: '/repartition/api/parametres/',
  },
  noyau: {
    identite: '/api/identite-etablissement/',
  },
}

let csrfToken = ''

export function setCsrfToken(token) {
  csrfToken = token || ''
}

function getCookie(name) {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) {
    return parts.pop().split(';').shift()
  }
  return ''
}

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData
  const headers = {
    Accept: 'application/json',
    ...(options.body && !isFormData ? { 'Content-Type': 'application/json' } : {}),
    ...options.headers,
  }

  const token = csrfToken || getCookie('csrftoken')
  if (token) {
    headers['X-CSRFToken'] = token
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    ...options,
    headers,
  })

  if (!response.ok) {
    let detail = ''
    try {
      const payload = await response.json()
      detail = payload.detail || payload.message || Object.values(payload).flat().join(' ')
    } catch {
      // Les pages HTML d'erreur Django ne doivent jamais etre affichees dans l'interface.
    }

    if (response.status === 403) {
      throw new Error('Votre session ou votre jeton de securite a expire. Actualisez la page puis reconnectez-vous.')
    }
    throw new Error(detail || `La requete a echoue (erreur ${response.status}).`)
  }

  if (response.status === 204) {
    return null
  }

  const data = await response.json()
  if (data?.csrf_token) {
    setCsrfToken(data.csrf_token)
  }
  return data
}

export const apiClient = {
  get: (path) => request(path),
  getBlob: async (path) => {
    const headers = {}
    const token = csrfToken || getCookie('csrftoken')
    if (token) {
      headers['X-CSRFToken'] = token
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
      credentials: 'include',
      headers,
    })

    if (!response.ok) {
      const message = await response.text()
      throw new Error(message || `Erreur API ${response.status}`)
    }

    return response.blob()
  },
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  postForm: (path, body) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
  patchForm: (path, body) => request(path, { method: 'PATCH', body }),
  delete: (path) => request(path, { method: 'DELETE' }),
}
