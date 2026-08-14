import { API_ENDPOINTS, apiClient } from '../../../services/apiClient'

function normalizeList(payload) {
  if (Array.isArray(payload)) {
    return payload
  }
  return payload?.results || []
}

export async function fetchEleves(params = {}) {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      searchParams.set(key, value)
    }
  })

  const query = searchParams.toString()
  return normalizeList(await apiClient.get(`${API_ENDPOINTS.eleves.list}${query ? `?${query}` : ''}`))
}

function buildQuery(params = {}) {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      searchParams.set(key, value)
    }
  })

  const query = searchParams.toString()
  return query ? `?${query}` : ''
}

export async function exportElevesXlsx(params = {}) {
  const blob = await apiClient.getBlob(`${API_ENDPOINTS.eleves.exportXlsx}${buildQuery(params)}`)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = `eleves_${new Date().toISOString().slice(0, 10)}.xlsx`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export async function fetchClasses() {
  return normalizeList(await apiClient.get(API_ENDPOINTS.eleves.classes))
}

export async function fetchElevesReferences() {
  return apiClient.get(API_ENDPOINTS.eleves.references)
}

function toEleveFormData(eleve) {
  const formData = new FormData()

  Object.entries(eleve).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      formData.append(key, value)
    }
  })

  return formData
}

export async function createEleve(eleve) {
  if (eleve.photo_file) {
    return apiClient.postForm(API_ENDPOINTS.eleves.list, toEleveFormData(eleve))
  }

  return apiClient.post(API_ENDPOINTS.eleves.list, eleve)
}

export async function updateEleve(id, eleve) {
  if (eleve.photo_file) {
    return apiClient.patchForm(API_ENDPOINTS.eleves.detail(id), toEleveFormData(eleve))
  }

  return apiClient.patch(API_ENDPOINTS.eleves.detail(id), eleve)
}

export async function deleteEleve(id) {
  return apiClient.delete(API_ENDPOINTS.eleves.detail(id))
}
