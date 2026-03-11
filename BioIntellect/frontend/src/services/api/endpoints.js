import apiClient from './axios.config'

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

const normalizeMessage = (message = {}) => ({
  ...message,
  id: message.id,
  message_content: message.message_content ?? message.content ?? '',
  sender_type: message.sender_type ?? message.role ?? 'llm',
})

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
  signOut: (scope = 'local') => apiClient.post('/auth/sign-out', { scope }),
  resetPassword: (email, redirect_to) =>
    apiClient.post('/auth/reset-password', { email, redirect_to }),
  updatePassword: (new_password, access_token, logout_all) =>
    apiClient.post('/auth/update-password', {
      new_password,
      access_token,
      logout_all,
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
  listMriResults: async (patientId) =>
    normalizeEnvelope(
      await apiClient.get('/clinical/mri/results', {
        params: { patient_id: patientId },
      })
    ),
  reviewResult: async (tableName, resultId, data) =>
    normalizeEnvelope(
      await apiClient.put(`/clinical/results/${tableName}/${resultId}/review`, data)
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
  update: async (id, data) =>
    normalizeEnvelope(
      await apiClient.put(`/users/patients/${id}`, data),
      normalizePatient
    ),
}

export const llmAPI = {
  createConversation: async (data) =>
    normalizeEnvelope(
      await apiClient.post('/llm/conversations', data),
      normalizeConversation
    ),
  sendMessage: async (data) => {
    const response = await apiClient.post(
      `/llm/conversations/${data.conversation_id}/messages`,
      {
        conversation_id: data.conversation_id,
        sender_type: 'user',
        message_content: data.message_content ?? data.messageContent ?? data.message,
        message_type: data.message_type ?? 'text',
      }
    )

    if (response?.success && response?.llm_response) {
      return {
        ...response,
        llm_response: normalizeMessage(response.llm_response),
      }
    }

    return {
      success: true,
      llm_response: normalizeMessage(response),
    }
  },
  getMessages: async (conversationId) =>
    normalizeEnvelope(
      await apiClient.get(`/llm/conversations/${conversationId}/history`),
      normalizeList(normalizeMessage)
    ),
  listConversations: async (params) =>
    normalizeEnvelope(
      await apiClient.get('/llm/conversations', { params }),
      normalizeList(normalizeConversation)
    ),
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
  llm: llmAPI,
  patients: patientsAPI,
}
