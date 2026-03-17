import { buildApiUrl } from './api/baseUrl'
import {
  ensureValidAccessToken,
  refreshAccessToken,
} from './auth/sessionManager'
import { getAccessToken } from './auth/sessionStore'

const buildCorrelationId = () => {
  try {
    return globalThis.crypto?.randomUUID?.() || `${Date.now()}`
  } catch {
    return `${Date.now()}-${Math.random().toString(36).slice(2)}`
  }
}

const buildAuthHeaders = async (baseHeaders = {}, tokenOverride = null) => {
  const token = tokenOverride || (await ensureValidAccessToken())
  const headers = {
    ...baseHeaders,
    'X-Correlation-ID':
      baseHeaders['X-Correlation-ID'] || buildCorrelationId(),
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  return headers
}

const fetchWithAuth = async (path, init = {}, retryOnUnauthorized = true) => {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: await buildAuthHeaders(init.headers || {}),
    credentials: 'include',
  })

  if (response.status === 401 && retryOnUnauthorized && getAccessToken()) {
    const refreshedToken = await refreshAccessToken()
    return fetch(buildApiUrl(path), {
      ...init,
      headers: await buildAuthHeaders(init.headers || {}, refreshedToken),
      credentials: 'include',
    })
  }

  return response
}

export const mriSegmentationService = {
  async getModelInfo() {
    const response = await fetchWithAuth('/clinical/model/info')

    if (!response.ok) {
      throw new Error('Failed to fetch model information')
    }

    return response.json()
  },

  async runSegmentation(files, options = {}) {
    const { t1, t1ce, t2, flair } = files

    if (!t1 || !t1ce || !t2 || !flair) {
      throw new Error('All 4 MRI modalities are required: T1, T1ce, T2, FLAIR')
    }

    const validExtensions = ['.nii', '.nii.gz']
    for (const [name, file] of Object.entries(files)) {
      const filename = file.name.toLowerCase()
      if (!validExtensions.some((extension) => filename.endsWith(extension))) {
        throw new Error(
          `Invalid file format for ${name}. Expected NIfTI (.nii or .nii.gz)`
        )
      }
    }

    const formData = new FormData()
    formData.append('t1', t1)
    formData.append('t1ce', t1ce)
    formData.append('t2', t2)
    formData.append('flair', flair)
    if (options.patientId) {
      formData.append('patient_id', options.patientId)
    }

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 300000)

    try {
      const response = await fetchWithAuth('/clinical/mri/segment', {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })

      clearTimeout(timeout)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Segmentation failed: ${response.status}`)
      }

      return response.json()
    } catch (error) {
      clearTimeout(timeout)

      if (error.name === 'AbortError') {
        throw new Error('Segmentation request timed out. Please try again.')
      }

      throw error
    }
  },

  async getPatientFriendlyResult(caseId) {
    const response = await fetchWithAuth(
      `/clinical/mri/result/${caseId}/patient-view`
    )

    if (!response.ok) {
      throw new Error('Failed to fetch patient-friendly result')
    }

    return response.json()
  },

  async getVisualizationArtifact(caseId, artifactType) {
    const validTypes = new Set(['image', 'labels'])
    if (!validTypes.has(artifactType)) {
      throw new Error('Unsupported MRI visualization artifact requested.')
    }

    const response = await fetchWithAuth(
      `/clinical/mri/visualization/${caseId}/${artifactType}`
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(
        errorData.detail || `Failed to load MRI ${artifactType} artifact`
      )
    }

    return response.arrayBuffer()
  },

  async downloadOutputFile(filename) {
    const response = await fetchWithAuth(`/files/${filename}/download`)

    if (!response.ok) {
      throw new Error('Failed to download output file')
    }

    return response.arrayBuffer()
  },

  formatVolume(volumeCm3, isPatient = false) {
    if (isPatient) {
      if (volumeCm3 < 1) return 'Small area detected'
      if (volumeCm3 < 10) return 'Moderate area detected'
      return 'Significant area detected'
    }

    return `${Number(volumeCm3 || 0).toFixed(2)} cm3`
  },

  getSeverityClassification(result) {
    const totalVolume = Number(result?.total_volume_cm3 || 0)
    const regions = Array.isArray(result?.regions) ? result.regions : []
    const hasEnhancing = regions.some(
      (region) => region.class_id === 3 && Number(region.volume_cm3 || 0) > 0
    )

    if (!result?.tumor_detected || totalVolume === 0) {
      return {
        level: 'normal',
        color: '#4CAF50',
        label: 'No Abnormalities Detected',
        description: 'AI analysis did not detect tumor presence.',
      }
    }

    if (totalVolume < 5 && !hasEnhancing) {
      return {
        level: 'low',
        color: '#8BC34A',
        label: 'Low Grade Finding',
        description: 'Small region detected. Recommend clinical correlation.',
      }
    }

    if (totalVolume < 20) {
      return {
        level: 'moderate',
        color: '#FFC107',
        label: 'Moderate Finding',
        description: 'Significant region detected. Further evaluation recommended.',
      }
    }

    return {
      level: 'high',
      color: '#FF9800',
      label: 'Significant Finding',
      description: 'Large region detected. Urgent clinical review recommended.',
    }
  },

  getPatientFriendlyClassName(clinicalName) {
    const mapping = {
      'Necrotic/Non-Enhancing Tumor Core': 'Central Region',
      'Peritumoral Edema': 'Surrounding Area',
      'Enhancing Tumor': 'Active Region',
    }
    return mapping[clinicalName] || 'Region of Interest'
  },
}

export default mriSegmentationService
