import apiClient from './axios.config';

/**
 * Domain-based API Clients
 * All calls go through Backend API Gateway with Resilience & Security.
 */

export const authAPI = {
    signUp: (data) => apiClient.post('/auth/signup', data),
    signIn: (email, password) => apiClient.post('/auth/signin', { email, password }),
    signOut: (scope = 'local') => apiClient.post('/auth/sign-out', { scope }), // Backend might not have this yet but good to have
    resetPassword: (email, redirect_to) => apiClient.post('/auth/reset-password', { email, redirect_to }),
    updatePassword: (new_password, access_token, logout_all) => apiClient.post('/auth/update-password', { new_password, access_token, logout_all }),
    getMe: () => apiClient.get('/auth/me')
};

export const clinicalAPI = {
    // Cases
    createCase: (caseData) => apiClient.post('/clinical/cases', caseData),
    getHistory: (patientId) => apiClient.get(`/clinical/patients/${patientId}/history`),

    // ECG
    createEcgSignal: (data) => apiClient.post('/clinical/ecg/signals', data),
    analyzeEcg: (scanId) => apiClient.post('/clinical/ecg/analyze', { scan_id: scanId }),
    listEcgResults: (patientId) => apiClient.get('/clinical/ecg/results', { params: { patient_id: patientId } }),

    // MRI
    createMriScan: (data) => apiClient.post('/clinical/mri/scans', data),
    analyzeMri: (scanId) => apiClient.post('/clinical/mri/analyze', { scan_id: scanId }),
    listMriResults: (patientId) => apiClient.get('/clinical/mri/results', { params: { patient_id: patientId } }),
    reviewResult: (tableName, resultId, data) => apiClient.put(`/clinical/results/${tableName}/${resultId}/review`, data),
};

export const analyticsAPI = {
    getSummary: () => apiClient.get('/analytics/summary'),
    getTrends: () => apiClient.get('/analytics/trends'),
    getAppointments: () => apiClient.get('/analytics/appointments'),
    updateAppointment: (id, data) => apiClient.put(`/analytics/appointments/${id}`, data),
};

export const filesAPI = {
    upload: (formData) => apiClient.post('/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    getDownloadUrl: (fileId) => apiClient.get(`/files/${fileId}/download`),
};

export const reportsAPI = {
    create: (data) => apiClient.post('/reports', data),
    list: (patientId) => apiClient.get('/reports', { params: { patient_id: patientId } }),
    approve: (reportId, notes) => apiClient.post(`/reports/${reportId}/approve`, { notes }),
};

export const geographyAPI = {
    getCountries: () => apiClient.get('/geography/countries'),
    getRegions: (countryId) => apiClient.get('/geography/regions', { params: { country_id: countryId } }),
    getHospitals: (regionId) => apiClient.get('/geography/hospitals', { params: { region_id: regionId } }),
};

export const usersAPI = {
    list: (type, params) => apiClient.get(`/users/${type}`, { params }),
    createPatient: (data) => apiClient.post('/users/patients', data),
    createDoctor: (data) => apiClient.post('/users/doctors', data),
    createAdministrator: (data) => apiClient.post('/users/administrators', data),
    getProfile: () => apiClient.get('/users/profile'),
    updateProfile: (data) => apiClient.put('/users/profile', data),
    uploadAvatar: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post('/users/avatar', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    }
};

export const patientsAPI = {
    list: (params) => apiClient.get('/users/patients', { params }),
    update: (id, data) => apiClient.put(`/users/patients/${id}`, data),
};

export const llmAPI = {
    createConversation: (data) => apiClient.post('/llm/conversations', data),
    sendMessage: (data) => apiClient.post(`/llm/conversations/${data.conversation_id}/messages`, { content: data.message_content }),
    getMessages: (conversationId) => apiClient.get(`/llm/conversations/${conversationId}/history`),
    listConversations: (params) => apiClient.get('/llm/conversations', { params }),
};

export default {
    auth: authAPI,
    clinical: clinicalAPI,
    analytics: analyticsAPI,
    files: filesAPI,
    reports: reportsAPI,
    geography: geographyAPI,
    users: usersAPI,
    llm: llmAPI,
    patients: patientsAPI
};
