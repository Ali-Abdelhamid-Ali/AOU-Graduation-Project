/**
 * API Service - Communicates with FastAPI Backend
 * All requests go through Backend -> Supabase (never Frontend -> Supabase directly)
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Session storage for auth token
let authToken = null;

export const setAuthToken = (token) => {
    authToken = token;
    if (token) {
        localStorage.setItem('biointellect_access_token', token);
    } else {
        localStorage.removeItem('biointellect_access_token');
    }
};

export const getAuthToken = () => {
    if (!authToken) {
        authToken = localStorage.getItem('biointellect_access_token');
    }
    return authToken;
};

// Base fetch wrapper with auth
const apiFetch = async (endpoint, options = {}) => {
    const token = getAuthToken();
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || error.message || 'API request failed');
    }
    
    return response.json();
};

// ============== AUTH API ==============

export const authAPI = {
    signUp: async (userData) => {
        return apiFetch('/auth/signup', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    },
    
    signIn: async (email, password) => {
        const result = await apiFetch('/auth/signin', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        
        if (result.success && result.session) {
            setAuthToken(result.session.access_token);
            localStorage.setItem('biointellect_refresh_token', result.session.refresh_token);
        }
        
        return result;
    },
    
    signOut: async () => {
        try {
            await apiFetch('/auth/signout', { method: 'POST' });
        } catch (e) {
            // Ignore errors on signout
        }
        setAuthToken(null);
        localStorage.removeItem('biointellect_refresh_token');
        localStorage.removeItem('biointellect_current_user');
        localStorage.removeItem('userRole');
    },
    
    refreshToken: async () => {
        const refreshToken = localStorage.getItem('biointellect_refresh_token');
        if (!refreshToken) return null;
        
        const result = await apiFetch('/auth/refresh', {
            method: 'POST',
            body: JSON.stringify({ refresh_token: refreshToken }),
        });
        
        if (result.success && result.session) {
            setAuthToken(result.session.access_token);
            localStorage.setItem('biointellect_refresh_token', result.session.refresh_token);
        }
        
        return result;
    },
    
    getCurrentUser: async () => {
        return apiFetch('/auth/me');
    },
    
    requestPasswordReset: async (email) => {
        return apiFetch('/auth/password-reset-request', {
            method: 'POST',
            body: JSON.stringify({ email }),
        });
    },
    
    updatePassword: async (newPassword) => {
        return apiFetch('/auth/password-update', {
            method: 'POST',
            body: JSON.stringify({ new_password: newPassword }),
        });
    },
};

// ============== USERS API ==============

export const usersAPI = {
    listDoctors: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/users/doctors${query ? '?' + query : ''}`);
    },
    
    getDoctor: async (doctorId) => {
        return apiFetch(`/users/doctors/${doctorId}`);
    },
    
    listNurses: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/users/nurses${query ? '?' + query : ''}`);
    },
    
    listAdministrators: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/users/administrators${query ? '?' + query : ''}`);
    },
    
    listSpecialties: async (category = null) => {
        const query = category ? `?category=${category}` : '';
        return apiFetch(`/users/specialties${query}`);
    },
    
    updateProfile: async (data) => {
        return apiFetch('/users/profile', {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },
};

// ============== PATIENTS API ==============

export const patientsAPI = {
    list: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/patients${query ? '?' + query : ''}`);
    },
    
    get: async (patientId) => {
        return apiFetch(`/patients/${patientId}`);
    },
    
    create: async (patientData) => {
        return apiFetch('/patients', {
            method: 'POST',
            body: JSON.stringify(patientData),
        });
    },
    
    update: async (patientId, patientData) => {
        return apiFetch(`/patients/${patientId}`, {
            method: 'PUT',
            body: JSON.stringify(patientData),
        });
    },
    
    delete: async (patientId) => {
        return apiFetch(`/patients/${patientId}`, { method: 'DELETE' });
    },
    
    getHistory: async (patientId) => {
        return apiFetch(`/patients/${patientId}/history`);
    },
};

// ============== CASES API ==============

export const casesAPI = {
    list: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/cases${query ? '?' + query : ''}`);
    },
    
    get: async (caseId) => {
        return apiFetch(`/cases/${caseId}`);
    },
    
    create: async (caseData) => {
        return apiFetch('/cases', {
            method: 'POST',
            body: JSON.stringify(caseData),
        });
    },
    
    update: async (caseId, caseData) => {
        return apiFetch(`/cases/${caseId}`, {
            method: 'PUT',
            body: JSON.stringify(caseData),
        });
    },
    
    archive: async (caseId) => {
        return apiFetch(`/cases/${caseId}/archive`, { method: 'POST' });
    },
};

// ============== FILES API ==============

export const filesAPI = {
    upload: async (file, caseId, patientId, fileType, description = null) => {
        const token = getAuthToken();
        const formData = new FormData();
        formData.append('file', file);
        formData.append('case_id', caseId);
        formData.append('patient_id', patientId);
        formData.append('file_type', fileType);
        if (description) formData.append('description', description);
        
        const response = await fetch(`${API_BASE_URL}/files/upload`, {
            method: 'POST',
            headers: token ? { 'Authorization': `Bearer ${token}` } : {},
            body: formData,
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
            throw new Error(error.detail || 'Upload failed');
        }
        
        return response.json();
    },
    
    get: async (fileId) => {
        return apiFetch(`/files/${fileId}`);
    },
    
    getDownloadUrl: async (fileId) => {
        return apiFetch(`/files/${fileId}/download-url`);
    },
    
    delete: async (fileId) => {
        return apiFetch(`/files/${fileId}`, { method: 'DELETE' });
    },
    
    listByCase: async (caseId) => {
        return apiFetch(`/files/case/${caseId}`);
    },
};

// ============== ECG API ==============

export const ecgAPI = {
    createSignal: async (signalData) => {
        return apiFetch('/ecg/signals', {
            method: 'POST',
            body: JSON.stringify(signalData),
        });
    },
    
    analyze: async (analysisData) => {
        return apiFetch('/ecg/analyze', {
            method: 'POST',
            body: JSON.stringify(analysisData),
        });
    },
    
    listResults: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/ecg/results${query ? '?' + query : ''}`);
    },
    
    getResult: async (resultId) => {
        return apiFetch(`/ecg/results/${resultId}`);
    },
    
    updateResult: async (resultId, data) => {
        return apiFetch(`/ecg/results/${resultId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },
    
    reviewResult: async (resultId, reviewData) => {
        return apiFetch(`/ecg/results/${resultId}/review`, {
            method: 'POST',
            body: JSON.stringify(reviewData),
        });
    },
};

// ============== MRI API ==============

export const mriAPI = {
    createScan: async (scanData) => {
        return apiFetch('/mri/scans', {
            method: 'POST',
            body: JSON.stringify(scanData),
        });
    },
    
    analyze: async (analysisData) => {
        return apiFetch('/mri/analyze', {
            method: 'POST',
            body: JSON.stringify(analysisData),
        });
    },
    
    listResults: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/mri/results${query ? '?' + query : ''}`);
    },
    
    getResult: async (resultId) => {
        return apiFetch(`/mri/results/${resultId}`);
    },
    
    updateResult: async (resultId, data) => {
        return apiFetch(`/mri/results/${resultId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },
    
    reviewResult: async (resultId, reviewData) => {
        return apiFetch(`/mri/results/${resultId}/review`, {
            method: 'POST',
            body: JSON.stringify(reviewData),
        });
    },
};

// ============== LLM/CHAT API ==============

export const llmAPI = {
    createConversation: async (conversationData) => {
        return apiFetch('/llm/conversations', {
            method: 'POST',
            body: JSON.stringify(conversationData),
        });
    },
    
    listConversations: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/llm/conversations${query ? '?' + query : ''}`);
    },
    
    getConversation: async (conversationId) => {
        return apiFetch(`/llm/conversations/${conversationId}`);
    },
    
    getMessages: async (conversationId, params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/llm/conversations/${conversationId}/messages${query ? '?' + query : ''}`);
    },
    
    sendMessage: async (messageData) => {
        return apiFetch('/llm/messages', {
            method: 'POST',
            body: JSON.stringify(messageData),
        });
    },
    
    requestAccess: async (requestData) => {
        return apiFetch('/llm/access-requests', {
            method: 'POST',
            body: JSON.stringify(requestData),
        });
    },
    
    respondToAccess: async (requestId, responseData) => {
        return apiFetch(`/llm/access-requests/${requestId}/respond`, {
            method: 'POST',
            body: JSON.stringify(responseData),
        });
    },
};

// ============== REPORTS API ==============

export const reportsAPI = {
    list: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/reports${query ? '?' + query : ''}`);
    },
    
    get: async (reportId) => {
        return apiFetch(`/reports/${reportId}`);
    },
    
    create: async (reportData) => {
        return apiFetch('/reports', {
            method: 'POST',
            body: JSON.stringify(reportData),
        });
    },
    
    update: async (reportId, reportData) => {
        return apiFetch(`/reports/${reportId}`, {
            method: 'PUT',
            body: JSON.stringify(reportData),
        });
    },
    
    approve: async (reportId, notes = null) => {
        const query = notes ? `?approval_notes=${encodeURIComponent(notes)}` : '';
        return apiFetch(`/reports/${reportId}/approve${query}`, { method: 'POST' });
    },
    
    sign: async (reportId) => {
        return apiFetch(`/reports/${reportId}/sign`, { method: 'POST' });
    },
};

// ============== NOTIFICATIONS API ==============

export const notificationsAPI = {
    list: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/notifications${query ? '?' + query : ''}`);
    },
    
    getUnreadCount: async () => {
        return apiFetch('/notifications/unread-count');
    },
    
    get: async (notificationId) => {
        return apiFetch(`/notifications/${notificationId}`);
    },
    
    markAsRead: async (notificationId) => {
        return apiFetch(`/notifications/${notificationId}`, {
            method: 'PUT',
            body: JSON.stringify({ is_read: true }),
        });
    },
    
    markAllAsRead: async () => {
        return apiFetch('/notifications/mark-all-read', { method: 'POST' });
    },
    
    archive: async (notificationId) => {
        return apiFetch(`/notifications/${notificationId}`, { method: 'DELETE' });
    },
};

// ============== ANALYTICS API ==============

export const analyticsAPI = {
    getDashboardStats: async (hospitalId = null) => {
        const query = hospitalId ? `?hospital_id=${hospitalId}` : '';
        return apiFetch(`/analytics/dashboard${query}`);
    },
    
    getPatientTrends: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/analytics/patients/trends${query ? '?' + query : ''}`);
    },
    
    getAnalysisSummary: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/analytics/analyses/summary${query ? '?' + query : ''}`);
    },
    
    getAuditLogs: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/analytics/audit-logs${query ? '?' + query : ''}`);
    },
};

// ============== GEOGRAPHY API ==============

export const geographyAPI = {
    listCountries: async () => {
        return apiFetch('/geography/countries');
    },
    
    getCountry: async (countryId) => {
        return apiFetch(`/geography/countries/${countryId}`);
    },
    
    listRegions: async (countryId = null) => {
        const query = countryId ? `?country_id=${countryId}` : '';
        return apiFetch(`/geography/regions${query}`);
    },
    
    getRegion: async (regionId) => {
        return apiFetch(`/geography/regions/${regionId}`);
    },
    
    listHospitals: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiFetch(`/geography/hospitals${query ? '?' + query : ''}`);
    },
    
    getHospital: async (hospitalId) => {
        return apiFetch(`/geography/hospitals/${hospitalId}`);
    },
    
    createHospital: async (hospitalData) => {
        return apiFetch('/geography/hospitals', {
            method: 'POST',
            body: JSON.stringify(hospitalData),
        });
    },
    
    updateHospital: async (hospitalId, hospitalData) => {
        return apiFetch(`/geography/hospitals/${hospitalId}`, {
            method: 'PUT',
            body: JSON.stringify(hospitalData),
        });
    },
};

// ============== HEALTH CHECK ==============

export const healthCheck = async () => {
    return apiFetch('/health');
};

export default {
    auth: authAPI,
    users: usersAPI,
    patients: patientsAPI,
    cases: casesAPI,
    files: filesAPI,
    ecg: ecgAPI,
    mri: mriAPI,
    llm: llmAPI,
    reports: reportsAPI,
    notifications: notificationsAPI,
    analytics: analyticsAPI,
    geography: geographyAPI,
    healthCheck,
    setAuthToken,
    getAuthToken,
};
