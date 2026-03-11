import axios from 'axios';
import { API_BASE_URL } from './baseUrl';
import { normalizeApiErrorPayload } from '@/utils/apiErrorUtils';

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

        if (!error.response) {
            const detail =
                error.code === 'ECONNABORTED'
                    ? `The API request timed out while contacting ${API_BASE_URL}.`
                    : `Cannot reach the API server at ${API_BASE_URL}.`;

            return Promise.reject(normalizeApiErrorPayload({
                detail,
                code: error.code || 'NETWORK_ERROR',
            }));
        }

        return Promise.reject(normalizeApiErrorPayload(error.response.data));
    }
);

export default apiClient;
