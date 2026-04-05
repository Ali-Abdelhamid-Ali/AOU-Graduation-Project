import apiClient from './axios.config'
import { API_BASE_URL } from './baseUrl'
import { getAccessToken } from '@/services/auth/sessionStore'

const normalizeEnvelope = (response, transform = (value) => value) => {
  if (response?.success !== undefined) {
    return {
      ...response,
      data:
        response.data !== undefined ? transform(response.data) : response.data,
    }
  }

  return {
    success: true,
    data: transform(response),
  }
}

const normalizePatient = (patient = {}) => ({
  ...patient,
  id: patient.id ?? patient.user_id,
  user_id: patient.user_id ?? patient.id,
  mrn: patient.mrn ?? patient.medical_record_number ?? null,
  medical_record_number: patient.medical_record_number ?? patient.mrn ?? null,
  photo_url: patient.photo_url ?? patient.avatar_url ?? null,
})

const normalizeCountry = (country = {}) => ({
  ...country,
  country_id: country.country_id ?? country.id,
  country_name: country.country_name ?? country.country_name_en,
  flag_url: country.flag_url ?? null,
})

const normalizeRegion = (region = {}) => ({
  ...region,
  region_id: region.region_id ?? region.id,
  region_name: region.region_name ?? region.region_name_en,
})

const normalizeHospital = (hospital = {}) => ({
  ...hospital,
  hospital_id: hospital.hospital_id ?? hospital.id,
  hospital_name: hospital.hospital_name ?? hospital.hospital_name_en,
})

const normalizeConversation = (conversation = {}) => ({
  ...conversation,
  id: conversation.id,
  title: conversation.title ?? 'Medical Consultation',
})

const normalizeMessage = (message = {}) => {
  // Handle null/undefined gracefully
  if (!message || typeof message !== 'object') {
    return {
      id: null,
      message_content: '',
      sender_type: 'llm',
    }
  }
  
  return {
    ...message,
    id: message.id ?? null,
    message_content: message.message_content ?? message.content ?? '',
    sender_type: message.sender_type ?? message.role ?? 'llm',
  }
}

const parseSseChunk = (chunk, handlers) => {
  const normalizedChunk = String(chunk || '').replace(/\r\n/g, '\n')
  const blocks = normalizedChunk.split('\n\n')

  blocks.forEach((block) => {
    if (!block.trim()) {
      return
    }

    const lines = block.split('\n')
    let eventName = 'message'
    const dataLines = []

    lines.forEach((line) => {
      if (line.startsWith('event:')) {
        eventName = line.slice(6).trim()
      }

      if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trim())
      }
    })

    const dataText = dataLines.join('\n')
    let payload = null
    try {
      payload = dataText ? JSON.parse(dataText) : null
    } catch {
      payload = { raw: dataText }
    }

    if (eventName === 'start') {
      handlers?.onStart?.(payload)
    } else if (eventName === 'token') {
      handlers?.onToken?.(payload)
    } else if (eventName === 'done') {
      handlers?.onDone?.(payload)
    } else if (eventName === 'error') {
      handlers?.onError?.(payload)
    }
  })
}

const normalizeList = (normalizer) => (items) =>
  Array.isArray(items) ? items.map(normalizer) : []

const normalizeUserMutation = (response, normalizer = (value) => value) => {
  const envelope = normalizeEnvelope(response, normalizer)
  return {
    ...envelope,
    id: envelope.data?.id,
    user_id: envelope.data?.user_id,
    mrn: envelope.data?.mrn,
  }
}

export const authAPI = {
  signUp: (data) => apiClient.post('/auth/signup', data),
  signIn: (email, password) =>
    apiClient.post('/auth/signin', { email, password }),
  refresh: () => apiClient.post('/auth/refresh', null, { skipAuthRefresh: true }),
  signOut: (scope = 'local') => apiClient.post('/auth/sign-out', { scope }),
  resetPassword: (email, redirect_to) =>
    apiClient.post('/auth/reset-password', { email, redirect_to }),
  updatePassword: (new_password, access_token, logout_all, current_password) =>
    apiClient.post('/auth/update-password', {
      new_password,
      access_token,
      logout_all,
      current_password,
    }),
  getMe: () => apiClient.get('/auth/me'),
}

export const clinicalAPI = {
  createCase: async (caseData) =>
    normalizeEnvelope(await apiClient.post('/clinical/cases', caseData)),
  getHistory: async (patientId) =>
    normalizeEnvelope(
      await apiClient.get(`/clinical/patients/${patientId}/history`)
    ),
  createEcgSignal: async (data) =>
    normalizeEnvelope(await apiClient.post('/clinical/ecg/signals', data)),
  analyzeEcg: async (signalId) =>
    normalizeEnvelope(
      await apiClient.post('/clinical/ecg/analyze', { signal_id: signalId })
    ),
  getEcgResult: async (resultId) =>
    normalizeEnvelope(await apiClient.get(`/clinical/ecg/results/${resultId}`)),
  listEcgResults: async (patientId) =>
    normalizeEnvelope(
      await apiClient.get('/clinical/ecg/results', {
        params: { patient_id: patientId },
      })
    ),
  createMriScan: async (data) =>
    normalizeEnvelope(await apiClient.post('/clinical/mri/scans', data)),
  createMriResult: async (data) =>
    normalizeEnvelope(await apiClient.post('/clinical/mri/results', data)),
  analyzeMri: async (scanId) =>
    normalizeEnvelope(
      await apiClient.post('/clinical/mri/analyze', { scan_id: scanId })
    ),
  getMriResult: async (resultId) =>
    normalizeEnvelope(await apiClient.get(`/clinical/mri/results/${resultId}`)),
  listMriResults: async (patientId) =>
    normalizeEnvelope(
      await apiClient.get('/clinical/mri/results', {
        params: { patient_id: patientId },
      })
    ),
}

export const analyticsAPI = {
  getSummary: () => apiClient.get('/analytics/dashboard'),
  getDashboardStats: () => apiClient.get('/analytics/dashboard'),
  getTrends: () => apiClient.get('/analytics/trends'),
  getAppointments: () => apiClient.get('/analytics/appointments'),
  createAppointment: async (data) =>
    normalizeEnvelope(await apiClient.post('/analytics/appointments', data)),
  updateAppointment: (id, data) =>
    apiClient.put(`/analytics/appointments/${id}`, data),
}

export const dashboardAPI = {
  getAdminOverview: async () =>
    normalizeEnvelope(await apiClient.get('/dashboard/admin/overview')),
  getDoctorOverview: async () =>
    normalizeEnvelope(await apiClient.get('/dashboard/doctor/overview')),
}

export const filesAPI = {
  upload: (formData) =>
    apiClient.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    }),
  getDownloadUrl: (fileId) => apiClient.get(`/files/${fileId}/download`),
}

export const reportsAPI = {
  create: async (data) => normalizeEnvelope(await apiClient.post('/reports', data)),
  list: async (patientId) =>
    normalizeEnvelope(
      await apiClient.get('/reports', { params: { patient_id: patientId } })
    ),
  approve: async (reportId, notes) =>
    normalizeEnvelope(
      await apiClient.post(`/reports/${reportId}/approve`, { notes })
    ),
}

export const geographyAPI = {
  getCountries: async () =>
    normalizeEnvelope(
      await apiClient.get('/geography/countries'),
      normalizeList(normalizeCountry)
    ),
  getRegions: async (countryId) =>
    normalizeEnvelope(
      await apiClient.get('/geography/regions', {
        params: { country_id: countryId },
      }),
      normalizeList(normalizeRegion)
    ),
  getHospitals: async (regionId) =>
    normalizeEnvelope(
      await apiClient.get('/geography/hospitals', {
        params: { region_id: regionId },
      }),
      normalizeList(normalizeHospital)
    ),
}

export const usersAPI = {
  list: (type, params) => apiClient.get(`/users/${type}`, { params }),
  listPaged: async (type, params) =>
    normalizeEnvelope(
      await apiClient.get(`/users/${type}/paged`, { params }),
      normalizeList((value) => value)
    ),
  createPatient: async (data) =>
    normalizeUserMutation(await apiClient.post('/users/patients', data), normalizePatient),
  createDoctor: async (data) =>
    normalizeUserMutation(await apiClient.post('/users/doctors', data)),
  createAdministrator: async (data) =>
    normalizeUserMutation(await apiClient.post('/users/administrators', data)),
  getProfile: async () => normalizeEnvelope(await apiClient.get('/users/profile')),
  updateProfile: async (data) =>
    normalizeEnvelope(await apiClient.put('/users/profile', data)),
  uploadAvatar: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/users/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export const patientsAPI = {
  list: async (params) =>
    normalizeEnvelope(
      await apiClient.get('/users/patients', { params }),
      normalizeList(normalizePatient)
    ),
  listPaged: async (params) =>
    normalizeEnvelope(
      await apiClient.get('/users/patients/paged', { params }),
      normalizeList(normalizePatient)
    ),
  update: async (id, data) =>
    normalizeEnvelope(
      await apiClient.put(`/users/patients/${id}`, data),
      normalizePatient
    ),
}

export const nlpChatAPI = {
  listModels: async () =>
    normalizeEnvelope(
      await apiClient.get('/nlp/models'),
      (payload) => payload || {}
    ),
  createConversation: async (projectId, data) =>
    normalizeEnvelope(
      await apiClient.post(`/nlp/chats/${projectId}/conversations`, data),
      (payload) => payload?.conversation || payload
    ),
  uploadAttachments: async (projectId, formData) =>
    normalizeEnvelope(
      await apiClient.post(`/nlp/chats/${projectId}/attachments`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 180000,
      }),
      (payload) => payload || {}
    ),
  listConversations: async (projectId, params) =>
    normalizeEnvelope(
      await apiClient.get(`/nlp/chats/${projectId}/conversations`, { params }),
      (payload) => normalizeList(normalizeConversation)(payload?.conversations || payload)
    ),
  getMessages: async (projectId, conversationId, params) =>
    normalizeEnvelope(
      await apiClient.get(`/nlp/chats/${projectId}/conversations/${conversationId}/messages`, { params }),
      (payload) => normalizeList(normalizeMessage)(payload?.messages || payload)
    ),
  sendMessage: async (projectId, conversationId, data) =>
    normalizeEnvelope(
      await apiClient.post(
        `/nlp/chats/${projectId}/conversations/${conversationId}/messages`,
        data
      ),
      (payload) => normalizeMessage(payload?.message || payload)
    ),
  // Non-streaming answer endpoint (recommended for stable UX)
  // Returns full response immediately without SSE
  answerQuestion: async (projectId, data) =>
    normalizeEnvelope(
      await apiClient.post(`/nlp/index/answer/${projectId}`, data),
      (payload) => ({
        conversation_id: payload?.conversation_id,
        answer: payload?.answer,
        full_prompt: payload?.full_prompt,
        chat_history: payload?.chat_history,
        user_message: payload?.user_message,
        assistant_message: normalizeMessage(payload?.assistant_message),
      })
    ),
  listConversationCount: async () =>
    normalizeEnvelope(
      await apiClient.get('/nlp/conversations/count'),
      (payload) => payload || {}
    ),
  archiveConversation: async (projectId, conversationId, reason) =>
    normalizeEnvelope(
      await apiClient.patch(
        `/nlp/chats/${projectId}/conversations/${conversationId}/archive`,
        null,
        { params: reason ? { reason } : undefined }
      ),
      (payload) => payload || {}
    ),
  // Legacy: Streaming is handled separately due to SSE requirements
  // Uses fetch to access response.body for streaming chunks
  streamAnswer: async (projectId, data, handlers = {}, signal) => {
    const token = getAccessToken()
    const response = await fetch(`${API_BASE_URL}/nlp/index/answer-stream/${projectId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      credentials: 'include',
      body: JSON.stringify(data),
      ...(signal ? { signal } : {}),
    })

    if (!response.ok) {
      let message = 'Failed to start streaming response'
      try {
        const payload = await response.json()
        message = payload?.detail || message
      } catch {
        // ignore parse failures and keep fallback message
      }
      throw new Error(message)
    }

    if (!response.body) {
      throw new Error('Streaming is not available in this browser')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    let isReading = true
    while (isReading) {
      const { value, done } = await reader.read()
      if (done) {
        if (buffer.trim()) {
          parseSseChunk(buffer, handlers)
        }
        isReading = false
        continue
      }

      buffer += decoder.decode(value, { stream: true })
      const chunks = buffer.split('\n\n')
      buffer = chunks.pop() || ''
      chunks.forEach((chunk) => parseSseChunk(`${chunk}\n\n`, handlers))
    }
  },
}

export default {
  auth: authAPI,
  clinical: clinicalAPI,
  analytics: analyticsAPI,
  dashboard: dashboardAPI,
  files: filesAPI,
  reports: reportsAPI,
  geography: geographyAPI,
  users: usersAPI,
  nlpChat: nlpChatAPI,
  patients: patientsAPI,
}
