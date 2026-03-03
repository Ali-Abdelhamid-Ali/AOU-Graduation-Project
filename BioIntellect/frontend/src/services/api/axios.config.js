import axios from 'axios';

const normalizeApiBaseUrl = (url) => {
    const fallback = 'http://localhost:8001/v1';
    const value = url || fallback;

    if (!import.meta.env.DEV) {
        return value;
    }

    return value
        .replace('://localhost:8000', '://localhost:8001')
        .replace('://127.0.0.1:8000', '://127.0.0.1:8001');
};

const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_URL);

/**
 * Resilient API Client with:
 * - Axios Interceptors (Token injection/Refresh)
 * - Soft Circuit Breaker
 * - Standardized Error Normalization
 */
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000, // 15s timeout
    headers: {
        'Content-Type': 'application/json',
    },
});

// ━━━━ SOFT CIRCUIT BREAKER STATE ━━━━
let failureCount = 0;
let isCircuitOpen = false;
const FAILURE_THRESHOLD = 5;
const COOLDOWN_MS = 30000; // 30s

// ━━━━ INTERCEPTORS ━━━━

apiClient.interceptors.request.use(
    (config) => {
        if (isCircuitOpen) {
            throw new Error('Circuit Breaker: API is temporarily unavailable due to repeated failures.');
        }

        const token = localStorage.getItem('biointellect_access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Audit Trace - Use fallback if crypto.randomUUID is not available
        try {
            config.headers['X-Correlation-ID'] = crypto.randomUUID();
        } catch (e) {
            // Fallback for browsers that don't support crypto.randomUUID
            config.headers['X-Correlation-ID'] = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        }

        return config;
    },
    (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
    (response) => {
        // Reset circuit on success
        failureCount = 0;
        isCircuitOpen = false;
        return response.data;
    },
    async (error) => {
        const originalRequest = error.config;

        // Handle Circuit Breaker
        if (error.response?.status >= 500 || error.code === 'ECONNABORTED') {
            failureCount++;
            if (failureCount >= FAILURE_THRESHOLD) {
                isCircuitOpen = true;
                setTimeout(() => { isCircuitOpen = false; failureCount = 0; }, COOLDOWN_MS);
            }
        }

        // Handle 401 Unauthorized (Token Expiry)
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            // Logic for silent token refresh would go here
        }

        return Promise.reject(error.response?.data || { detail: 'Network Error' });
    }
);

export default apiClient;
