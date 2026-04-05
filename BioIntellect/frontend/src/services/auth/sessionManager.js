import axios from 'axios'

import { API_BASE_URL } from '@/services/api/baseUrl'
import { normalizeApiErrorPayload } from '@/utils/apiErrorUtils'

import {
  clearAccessSession,
  clearPersistedSensitiveTokens,
  clearRecoveryToken,
  getAccessToken,
  isAccessTokenExpiringSoon,
  notifyAuthFailure,
  setAccessSession,
} from './sessionStore'

const refreshClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

let refreshPromise = null
let sessionExpiryPromise = null

const toNormalizedSessionError = (error) => {
  if (error?.error_code || error?.message) {
    return error
  }

  if (error?.response?.data) {
    return normalizeApiErrorPayload(error.response.data)
  }

  return normalizeApiErrorPayload({
    detail: 'Your session has expired. Please sign in again.',
    code: 'SESSION_EXPIRED',
  })
}

const redirectToLogin = () => {
  if (typeof window === 'undefined') {
    return
  }

  if (window.location.pathname !== '/login') {
    window.location.assign('/login')
  }
}

const applyRefreshResponse = (payload) => {
  if (!payload?.success || !payload?.session?.access_token) {
    throw new Error(payload?.message || 'Session refresh failed')
  }

  setAccessSession({
    accessToken: payload.session.access_token,
    expiresAt: payload.session.expires_at,
  })

  return payload.session.access_token
}

export const handleSessionExpiry = async () => {
  if (sessionExpiryPromise) {
    return sessionExpiryPromise
  }

  sessionExpiryPromise = (async () => {
    clearAccessSession()
    clearRecoveryToken()
    clearPersistedSensitiveTokens()
    await notifyAuthFailure()
    redirectToLogin()
  })().finally(() => {
    sessionExpiryPromise = null
  })

  return sessionExpiryPromise
}

export const refreshAccessToken = async () => {
  if (refreshPromise) {
    return refreshPromise
  }

  refreshPromise = refreshClient
    .post('/auth/refresh')
    .then(({ data }) => applyRefreshResponse(data))
    .catch(async (error) => {
      try {
        await handleSessionExpiry()
      } catch (sessionExpiryError) {
        console.error('Session expiry handler failed:', sessionExpiryError)
      }
      throw toNormalizedSessionError(error)
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

export const ensureValidAccessToken = async (bufferMs = 60_000) => {
  const currentToken = getAccessToken()
  if (!currentToken) {
    return null
  }

  if (!isAccessTokenExpiringSoon(bufferMs)) {
    return currentToken
  }

  return refreshAccessToken()
}
