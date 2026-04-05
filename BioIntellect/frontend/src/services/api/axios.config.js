import axios from 'axios'

import {
  ensureValidAccessToken,
  refreshAccessToken,
} from '@/services/auth/sessionManager'
import { getAccessToken } from '@/services/auth/sessionStore'
import { normalizeApiErrorPayload } from '@/utils/apiErrorUtils'

import { API_BASE_URL } from './baseUrl'

const LOOPBACK_BASE_PATTERN = /^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?/i
const DEFAULT_API_TIMEOUT_MS = 60000 // Increased from 15s to 60s for LLM generation
const API_TIMEOUT_MS = Number(
  import.meta.env.VITE_API_TIMEOUT_MS || DEFAULT_API_TIMEOUT_MS
)

const buildAlternateLoopbackBase = (value) => {
  const source = String(value || '').trim()
  if (!LOOPBACK_BASE_PATTERN.test(source)) {
    return null
  }

  if (source.includes('127.0.0.1')) {
    return source.replace('127.0.0.1', 'localhost')
  }

  if (source.includes('localhost')) {
    return source.replace('localhost', '127.0.0.1')
  }

  return null
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT_MS,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

let failureCount = 0
let isCircuitOpen = false
const FAILURE_THRESHOLD = 5
const COOLDOWN_MS = 30000

const buildCorrelationId = () => {
  try {
    return crypto.randomUUID()
  } catch {
    return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
  }
}

const isRefreshRequest = (config = {}) =>
  String(config.url || '').includes('/auth/refresh') ||
  config.skipAuthRefresh === true

const shouldAttachToken = (config = {}) => {
  const url = String(config.url || '')
  return !isRefreshRequest(config) && !url.includes('/auth/signin')
}

apiClient.interceptors.request.use(
  async (config) => {
    if (isCircuitOpen) {
      throw new Error(
        'Circuit Breaker: API is temporarily unavailable due to repeated failures.'
      )
    }

    if (shouldAttachToken(config)) {
      const token = await ensureValidAccessToken()
      if (token) {
        config.headers = config.headers || {}
        config.headers.Authorization = `Bearer ${token}`
      }
    }

    config.headers = config.headers || {}
    config.headers['X-Correlation-ID'] =
      config.headers['X-Correlation-ID'] || buildCorrelationId()
    config.withCredentials = true

    return config
  },
  (error) => Promise.reject(error)
)

apiClient.interceptors.response.use(
  (response) => {
    failureCount = 0
    isCircuitOpen = false
    return response.data
  },
  async (error) => {
    const originalRequest = error.config || {}

    if (error.response?.status >= 500 || error.code === 'ECONNABORTED') {
      failureCount += 1
      if (failureCount >= FAILURE_THRESHOLD) {
        isCircuitOpen = true
        setTimeout(() => {
          isCircuitOpen = false
          failureCount = 0
        }, COOLDOWN_MS)
      }
    }

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !isRefreshRequest(originalRequest) &&
      Boolean(getAccessToken())
    ) {
      originalRequest._retry = true

      try {
        const refreshedToken = await refreshAccessToken()
        originalRequest.headers = originalRequest.headers || {}
        originalRequest.headers.Authorization = `Bearer ${refreshedToken}`
        originalRequest.withCredentials = true
        return apiClient(originalRequest)
      } catch (refreshError) {
        return Promise.reject(refreshError)
      }
    }

    if (!error.response) {
      const alternateBaseUrl = buildAlternateLoopbackBase(
        originalRequest.baseURL || API_BASE_URL
      )

      if (alternateBaseUrl && !originalRequest._loopbackRetryAttempted) {
        return apiClient({
          ...originalRequest,
          _loopbackRetryAttempted: true,
          baseURL: alternateBaseUrl,
        })
      }

      const detail =
        error.code === 'ECONNABORTED'
          ? `The API request timed out while contacting ${API_BASE_URL}. The backend accepted the connection but did not respond in time.`
          : `Cannot reach the API server at ${API_BASE_URL}. Check the backend process and the Vite dev proxy target.`

      return Promise.reject(
        normalizeApiErrorPayload({
          detail,
          code: error.code || 'NETWORK_ERROR',
        })
      )
    }

    return Promise.reject(normalizeApiErrorPayload(error.response.data))
  }
)

export default apiClient
